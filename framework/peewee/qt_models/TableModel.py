from PyQt5 import QtWidgets, QtCore
from typing import Type, List, Dict, Optional, Any
from ... import global_const
from ...peewee import BaseModel, IntEnumField
import peewee
from ...common import WidgetFunctions

class TableModel(QtCore.QAbstractItemModel):
    """Базовая модель для редактирования таблицы БД с помощью peewee"""
    def __init__(self, peewee_class: Type[BaseModel], parent: QtCore.QObject = None):
        super().__init__(parent)
        # Указатель на базовый класс peewee
        self.peewee_class = peewee_class
        # Лист с именами столбцов таблицы (за исключением id)
        self.fields: List[str] = list(peewee_class._meta.fields.keys())[1:]
        # Лист с записями таблицы (экземплярами базового класса peewee_class)
        self._data: List[BaseModel] = []
        # Словарь свзывания id записи с экземпляром класса peewee_class (для быстрого поиска по id)
        self._idToPeeweeInstance: Dict[int, BaseModel] = {}
        # Словарь с делегатами для столбцов
        self._delegates:Dict[str, QtWidgets.QStyledItemDelegate] = {}
        # Курсив для пустых значений
        _font = QtWidgets.qApp.font()
        _font.setItalic(True)
        self.special_font = _font

    def columnCount(self, parent=QtCore.QModelIndex) -> int:
        """Получение количества столбцов модели"""
        return len(self.fields)

    def rowCount(self, parent=QtCore.QModelIndex()) -> int:
        """Получение количества строк модели"""
        return len(self._data)

    def index(self, row: int, column: int, parent=QtCore.QModelIndex()) -> QtCore.QModelIndex:
        """Получение индекса модели по номерам строки и столбца соответственно"""
        if self.hasIndex(row, column, parent):
            return self.createIndex(row, column, self._data[row])
        return QtCore.QModelIndex()

    def parent(self, index) -> QtCore.QModelIndex:
        """Получение родительского индекса для index (для табличной возвращает пустой QModelIndex)"""
        return QtCore.QModelIndex()

    def flags(self, index) -> int:
        """Получение флагов для элемента модели с индексом index"""
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsEditable

    def headerData(self, section:int, orientation:int, role:int=QtCore.Qt.DisplayRole) -> Any:
        """Получение названий заголовков для столбцов и строк в зависимости от orientation"""
        if role != QtCore.Qt.DisplayRole:
            return QtCore.QVariant()
        if orientation == QtCore.Qt.Horizontal:
            # Получаем русскоязычное название поля
            verbose_name = self.peewee_class._meta.fields[self.fields[section]].verbose_name
            if not verbose_name is None and len(verbose_name.strip())==0:
                return self.fields[section]
            return verbose_name
        return None

    def data(self, index: QtCore.QModelIndex, role:int=QtCore.Qt.DisplayRole) -> Any:
        """Получение данных элемента модели с индексом index и ролью представления role"""
        if not index.isValid():
            return QtCore.QVariant()
        _record = self._data[index.row()]
        return WidgetFunctions.model_data_from_instance(_record, self.fields[index.column()], role, self.special_font)

    def setData(self, index, value, role:int = QtCore.Qt.EditRole) -> bool:
        """Установление значения value для элемента модели с индексом index и ролью role"""
        if not index.isValid() or role != QtCore.Qt.EditRole:
            return False
        _record = self._data[index.row()]
        field:peewee.Field = self.peewee_class._meta.fields[self.fields[index.column()]]
        old_value = getattr(_record, field.name)
        if value == old_value:
            return False
        # Для необязательных текстовых полей, вместо пустой стороки пишем None
        if isinstance(field, peewee.CharField) and field.null and len(value) == 0:
            value = None
        setattr(_record, field.name, value)
        try:
            _record.save()
        except peewee.InternalError as px:
            print(str(px))
            return False
        self.dataChanged.emit(index, index, [QtCore.Qt.DisplayRole, QtCore.Qt.EditRole])
        return True

    def removeRows(self, row:int, count:int, parent:QtCore.QModelIndex=QtCore.QModelIndex()) -> bool:
        """Удаляет count строк, начиная с row из таблицы"""
        self.beginRemoveRows(parent, row, row + count - 1)
        for _ in range(count):
            _record = self._data.pop(row)
            del self._idToPeeweeInstance[_record.id]
            try:
                _record.delete_instance()
            except peewee.InternalError as px:
                print(str(px))
                return False
        self.endRemoveRows()
        return True

    def get_instance_by_id(self, id: int) -> BaseModel:
        """Возвращает экземпляр peewee_class с искомым id"""
        return self._idToPeeweeInstance[id]

    def load_data(self):
        """Загрузка данных из ОРМ (БД)"""
        self._data.clear()
        for element in self.peewee_class.select():
            self._data.append(element)
            self._idToPeeweeInstance[element.id] = element

    def refresh(self):
        """Полное обноаление данных модели"""
        self.beginResetModel()
        self.load_data()
        self.endResetModel()

    def appendRows(self, peewee_instances:List[BaseModel]) -> bool:
        """Добавление строк в БД"""
        # Проверка элементов списка
        for peewee_instance in peewee_instances:
            if not isinstance(peewee_instance, self.peewee_class):
                print(f'Ошибка: объект {peewee_instance} не является экземпляром класса {type(self.peewee_class)}')
                return False
            # Если есть незаписанные значения - сохранить
            if len(peewee_instance.dirty_fields) > 0:
                try:
                    peewee_instance.save()
                except peewee.InternalError as px:
                    print(str(px))
                    return False
        # Вставка в модель
        self.beginInsertRows(QtCore.QModelIndex(), len(self._data), len(self._data) + len(peewee_instances) - 1)
        self._data.extend(peewee_instances)
        self.endInsertRows()
        return True


