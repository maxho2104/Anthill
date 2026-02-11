from tabnanny import verbose

from PyQt5 import QtWidgets, QtCore
from typing import Optional, Callable, Union, Type, List, Dict, Any
from framework import BaseModel, DBManager, global_const, StrExplainableIntEnum
import peewee
import enum
import datetime

class WhereExpression:
    """Представление условия фильтра"""
    @enum.unique
    class OperationType(enum.IntEnum):
        less            = 0
        less_or_equal   = 1
        equal           = 2
        not_equal       = 3
        more_or_equal   = 4
        more            = 5
        starts_with     = 6
        contains        = 7
        ends_with       = 8

        @staticmethod
        def _get_explanation_dict():
            """Возвращает словарь с текстовыми описаниями значений (переопределять в потомках)"""
            return {
                0: 'меньше',
                1: 'меньше или равно',
                2: 'равно',
                3: 'не равно',
                4: 'больше',
                5: 'больше или равно',
                6: 'начинается с',
                7: 'содержит',
                8: 'оканчивается на',
            }

        def _get_str(self) -> str:
            """Возвращает текстовое описание значения"""
            explanation = self._get_explanation_dict()
            return explanation[self.value]

        def __str__(self):
            return self._get_str()

    def __init__(self, **kwargs):
        self._field = None,
        self._operation = None
        self._value = None
        for kwarg in kwargs:
            if kwarg == 'field':
                self._field = kwargs[kwarg]
                continue
            elif kwarg == 'operation':
                self._operation = kwargs[kwarg]
                continue
            elif kwarg == 'value':
                self._value = kwargs[kwarg]
                continue

    @property
    def field(self):
        return self._field
    @field.setter
    def field(self, f:Union[peewee.Alias, peewee.Field, peewee.Column, None]):
        self._field = f

    @property
    def operation(self):
        return self._operation
    @operation.setter
    def operation(self, op:OperationType):
        self._operation = op

    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, val:Any):
        self._value = val

    def get_field_type(self):
        """Получить тип поля"""
        res_field = self._field
        # Избавимся от алиасов
        while isinstance(res_field, peewee.Alias):
            res_field = res_field.node
        return type(res_field)

    def to_peewee_expression(self)->Optional[peewee.Expression]:
        """Преобразование из внутреннего формата в формат peewee Excpression"""
        if self._operation == self.OperationType.less:
            return peewee.Expression(lhs=self._field, op='<', rhs=self.value)
        elif self._operation == self.OperationType.less_or_equal:
            return peewee.Expression(lhs=self._field, op='<=', rhs=self.value)
        elif self._operation == self.OperationType.equal:
            return peewee.Expression(lhs=self._field, op='=', rhs=self.value)
        elif self._operation == self.OperationType.not_equal:
            return peewee.Expression(lhs=self._field, op='!=', rhs=self.value)
        elif self._operation == self.OperationType.more_or_equal:
            return peewee.Expression(lhs=self._field, op='>=', rhs=self.value)
        elif self._operation == self.OperationType.more:
            return peewee.Expression(lhs=self._field, op='>', rhs=self.value)
        elif self._operation == self.OperationType.starts_with:
            return self._field.startswith(peewee.fn.LOWER(self._value))
        elif self._operation == self.OperationType.contains:
            return self._field.contains(peewee.fn.LOWER(self.value))
            #return self._field.contains(self.value)
        elif self._operation == self.OperationType.ends_with:
            return self._field.endswith(peewee.fn.LOWER(self._value))
        return None

class BatchedQueryModel(QtCore.QAbstractTableModel):
    """Модель для работы с данными по запросу (загрузка осуществляется пачками по batch_size записей)"""
    batch_size:int = 50
    query: peewee.ModelSelect = None
    _header_names:List[str] = None
    # Пользовательская функция представления данных в таблице (аналог data())
    _user_data_func: Callable[[List[Dict[str,Any]],QtCore.QModelIndex, int], Any] = None
    # Словарь сопоставления имен полей запроса с его русскоязычным названием (для отображения в фильтрах)
    _verbose_query_fields: Dict[str, str] = None
    _loaded_records: int = 0    # количество загруженных записей
    _total_records: int = 0     # общее количество записей в БД, соответсвующих условиям запроса
    _data: List[Dict[str,Any]] = [] # внутренние данные модели
    _where_expressions: List[WhereExpression] = []
    loading: bool = False

    def __init__(self, query:peewee.ModelSelect=None, header_names:List[str]=None,
                 user_data_func:Callable[[List[Dict[str,Any]],QtCore.QModelIndex, int], Any]=None,
                 where_expressions:List[WhereExpression]=None, verbose_names:Dict[str, str]=None, parent=None):
        super().__init__(parent)
        if not query is None:
            self.query = query
        if not header_names is None:
            self._header_names = header_names
        if not user_data_func is None:
            self._user_data_func = user_data_func
        if not verbose_names is None:
            self._verbose_query_fields = verbose_names
        if not where_expressions is None:
            self._where_expressions = where_expressions

        # Курсив для пустых значений
        _font = QtWidgets.qApp.font()
        _font.setItalic(True)
        self.special_font = _font


    def base_peewee_model(self) -> Optional[Type[BaseModel]]:
        """Получение базовой модели, с которой начинается запрос, т.е. при запросе 'Model.select(...)'
        вернет тип 'Model'"""
        if not self.query is None:
            return type(self.query.model)
        return None

    def selected_fields_names(self) -> Optional[List[str]]:
        """Возвращает имена столбцов запроса (полей или алиасов)"""
        if not self.query is None:
            return [field.name for field in self.query.selected_columns]
        return None

    def _get_expression(self)->Optional[peewee.Expression]:
        """Получение выражений для фильтров peewee (в where(...)) из списка имеющихся (self._where_expressions)"""
        if len(self._where_expressions) == 0: return None
        total_expr:peewee.Expression = None
        for where_expression in self._where_expressions:
            curr_expr = where_expression.to_peewee_expression()
            if not curr_expr is None:
                if total_expr is None:
                    total_expr = curr_expr
                else:
                    total_expr = (total_expr & curr_expr)
        return total_expr

    def _get_working_query(self)->peewee.ModelSelect:
        """Получение запроса для работы (вместе с условиями для where(...))"""
        expression = self._get_expression()
        if expression is None:
            return self.query
        return self.query.where(expression)

    def verbose_name_for_field(self, field_name:str)->Optional[str]:
        """Возвращает русскоязычное название для столбца в запросе"""
        # Если запроса не существует - вернем None
        if not field_name in self.selected_fields_names(): return None
        # Если имя поля есть в специальном словаре - вернем его
        if (not self._verbose_query_fields is None) and (field_name in self._verbose_query_fields):
            return self._verbose_query_fields[field_name]
        # Получим verbose_name из поля модели, получаемого из запроса
        field = self.query.selected_columns[self.selected_fields_names().index(field_name)]
        # Если поле - alias, избавимся от алиасов
        while isinstance(field, peewee.Alias):
            field = field.node
        if isinstance(field, peewee.Field) and not field.verbose_name is None:
            return field.verbose_name
        return field_name

    def rowCount(self, parent=QtCore.QModelIndex())->int:
        """Возвращает количество строк в модели"""
        return len(self._data)

    def _gather_data_from_database(self, working_query:peewee.ModelSelect) -> Optional[List[Dict[str, Any]]]:
        # Получение порции данных в модель из базы
        result = []
        try:
            for record in (working_query
                    # TODO добавить сортировку
                    #.order_by(SQL('outgoing_doc_date').desc())
                    .limit(self.batch_size)
                    .offset(self._loaded_records)
                    .objects()):
                record_data = {}
                for field_name in self.selected_fields_names():
                    field_value = getattr(record, field_name)
                    record_data[field_name] = field_value
                result.append(record_data)
        except peewee.PeeweeException as e:
            print(f'Ошибка загрузки данных: {e}')
        return  result

    def _load_batch(self):
        """Загружает одну порцию данных (количество записей, указанных в self.batch_size) из базы и добавляет в модель"""
        # Если запрос отсутствует или база не подключена - выход
        if self.query is None or not DBManager().connected: return

        self.loading = True

        working_query = self._get_working_query()

        # Загрузка первой партии данных
        if self._total_records == 0:
            # Если заголовки столбцов не были установлены - устанавливаем дефолтные
            if self._header_names is None:
                self._header_names = [self.verbose_name_for_field(field_name) for field_name in self.selected_fields_names()]
            # Получаем общее количество записей
            # Делаем запрос для подсчета
            counting_query = (working_query.model.select(peewee.fn.COUNT(working_query.model.id).alias('count'))
                              .join(working_query, on=(working_query.model.id == working_query.c.id)))

            self._total_records = counting_query.scalar()
            self._loaded_records = 0

        # Загружаем порцию данных с учетом уже загруженных записей

        new_records = self._gather_data_from_database(working_query)

        # Добавляем загруженные записи в модель
        self.beginInsertRows(QtCore.QModelIndex(), len(self._data), len(self._data) + len(new_records) - 1)
        self._data.extend(new_records)
        self.endInsertRows()
        self._loaded_records = len(self._data) # Увеличиваем счетчик загруженных записей

        self.loading = False

    def columnCount(self, parent=QtCore.QModelIndex()) -> int:
        """Возвращает количество колонок"""
        if self._header_names is None: return 0
        return len(self._header_names)

    def canFetchMore(self, parent=QtCore.QModelIndex())->bool:
        """Сообщает представлению, можно ли загрузить больше данных"""
        return self._loaded_records < self._total_records and not self.loading

    def fetchMore(self, parent=QtCore.QModelIndex()):
        """Загружает следующую порцию данных"""
        if self.loading or self._loaded_records >= self._total_records:
            return
        # Загружаем следующую порцию данных
        self._load_batch()

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """Возвращает заголовки колонок"""
        if role == QtCore.Qt.DisplayRole and orientation == QtCore.Qt.Horizontal:
            return self._header_names[section]
        return None

    def _default_data(self, index, role=QtCore.Qt.DisplayRole):
        if (not index.isValid() or role != QtCore.Qt.DisplayRole
                or index.row() >= len(self._data)
                or index.column() >= len(self.selected_fields_names())):
            return None
        data = self._data[index.row()][self.selected_fields_names()[index.column()]]
        if data is None:
            return global_const.defaultNoneDisplayedText
        if isinstance(data, datetime.datetime):
            return data.strftime('%H:%M %d.%m.%Y')
        if isinstance(data, datetime.date):
            return data.strftime('%d.%m.%Y')
        if isinstance(data, datetime.time):
            return data.strftime('%H:%M')
        if isinstance(data, bool):
            if data:
                return global_const.defaultTrueDisplayedText
            else:
                return global_const.defaultFalseDisplayedText
        if isinstance(data, StrExplainableIntEnum):
            return str(data)
        return data



    def data(self, index, role=QtCore.Qt.DisplayRole):
        """Возвращает данные для указанной ячейки"""

        # Если присутствует пользовательская функция - возвращаем ее результат
        if not self._user_data_func is None:
            return self._user_data_func(self._data, index, role)
        else:
            return self._default_data(index, role)

    def refresh(self):
        """Обновляет данные в модели"""
        self.beginResetModel()
        self._data.clear()
        self._total_records = 0
        self._load_batch()
        self.endResetModel()
