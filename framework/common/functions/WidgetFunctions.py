import peewee
from PyQt5 import QtWidgets, QtCore, QtGui
from typing import Any, Dict, Optional, Type
from peewee import ForeignKeyField, Expression
from ...peewee import IntEnumField, BaseModel
from ... import global_const
from ..utils import DBManager
from . import DateAndTime

"""Различные функции для работы с видлжетами"""

def makeCalendar() -> QtWidgets.QCalendarWidget:
    """Создание виджета календаря
    Возвращает:
        QCalendarWidget
    """
    calendar = QtWidgets.QCalendarWidget()
    calendar.setFirstDayOfWeek(QtCore.Qt.Monday)
    calendar.setGridVisible(True)
    return calendar

def default_fill_date_edit(date_edit_ref: QtWidgets.QDateEdit):
    """Заполнение DateEdit'а по умолчанию, с отображением календаря
    Параметры:
        date_edit_ref - ссылка на DateEdit
    """
    date_edit_ref.setMinimumDate(QtCore.QDate(1900, 1, 1))
    date_edit_ref.setMaximumDate(QtCore.QDateTime.currentDateTime().date())
    date_edit_ref.setDate(QtCore.QDateTime.currentDateTime().date())
    date_edit_ref.setCalendarWidget(makeCalendar())
    date_edit_ref.setCalendarPopup(True)

def default_fill_datetime_edit(datetime_edit_ref: QtWidgets.QDateTimeEdit):
    """Заполнение DateTimeEdit'а по умолчанию, с отображением календаря
    Параметры:
        datetime_edit_ref - ссылка на DateTimeEdit
    """
    datetime_edit_ref.setMinimumDateTime(QtCore.QDateTime(QtCore.QDate(1900,1,1),QtCore.QTime(0,0)))
    datetime_edit_ref.setMaximumDateTime(QtCore.QDateTime.currentDateTime())
    datetime_edit_ref.setDateTime(QtCore.QDateTime.currentDateTime())
    datetime_edit_ref.setCalendarWidget(makeCalendar())
    datetime_edit_ref.setCalendarPopup(True)

def set_combo_value(combo_ref:QtWidgets.QComboBox, value:Any, role = QtCore.Qt.UserRole) -> bool:
    """Установка текущего элемента комбобокса по значению data
    Параметры:
        combo_ref - ссылка на QComboBox,
        role - роль Qt, для которой устанавливаются значения (по умолчанию - Qt.UserRole)
    """
    index = combo_ref.findData(value, role)
    if index > -1:
        combo_ref.setCurrentIndex(index)
        return True
    return False

def fill_combobox(data:Dict[str,Any], combo_ref:QtWidgets.QComboBox, sort:bool=False, set_editable:bool=False):
    """Заполнение итемов комбобокса
    Параметры:
        data - словарь{Текст итема : занчение},
        combo_ref - ссылка на QComboBox,
        sort - флаг необходимости сортировки,
        set_editable - флаг необходимости сделать осуществлять поиск по элементам QComboBox"а ручным вводом
    """
    combo_ref.clear()
    data_keys = list(data.keys())
    if sort:
        data_keys.sort()
    for key in data_keys:
        combo_ref.addItem(key, data[key])
    if set_editable:
        combo_ref.setEditable(True)
        combo_ref.completer().setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        combo_ref.completer().setFilterMode(QtCore.Qt.MatchContains)

def fill_boolean_combobox(_field:Type[peewee.BooleanField], combo_ref:QtWidgets.QComboBox):
    """Заполнение комбобокса с булеановскими значениями
            Параметры:
                field - поле булеановских значений,
                combo_ref - ссылка на QComboBox
            """
    fill_combobox({global_const.defaultTrueDisplayedText:True,global_const.defaultFalseDisplayedText:False}, combo_ref)
    if _field.null:
        combo_ref.insertItem(0, global_const.defaultNoneDisplayedText, None)

def fill_int_enum_combobox(_field:Type[IntEnumField], combo_ref:QtWidgets.QComboBox):
    """Заполнение комбобокса со значениями пречислений
        Параметры:
            field - поле перечислений,
            combo_ref - ссылка на QComboBox
        """
    fill_combobox({str(value):value for value in _field.enum_class}, combo_ref)
    if _field.null:
        combo_ref.insertItem(0, global_const.defaultNoneDisplayedText, None)

def fill_foreign_combobox(_field:Type[ForeignKeyField], combo_ref:QtWidgets.QComboBox, filter_expression:Optional[Expression]=None):
    """Заполнение комбобокса со значениями внешних ключей
            Параметры:
                field - поле внешнего ключа,
                combo_ref - ссылка на QComboBox,
                filter_expression - выражение для фильтрации значений в запросе к БД
            """
    if not DBManager().connected:
        return
    # Получаем значения внешних ключей
    if filter_expression is None:
        query = _field.rel_model.select()
    else:
        query = _field.rel_model.select().where(filter_expression)
    val_dict: Dict[str, int] = {}
    for element in query:
        val_dict[element.representation()] = element.id
    # Заполняем QComboBox
    fill_combobox(val_dict, combo_ref, sort=True, set_editable=True)
    if _field.null:
        combo_ref.insertItem(0, global_const.defaultNoneDisplayedText, None)

def model_data_from_instance(instance:BaseModel, attr_name:str, role:int = QtCore.Qt.DisplayRole, special_font:Optional[QtGui.QFont]=None) -> Any:
    """Получение данных для модели Qt из экземпляра класса peewee по соответсвующего имени поля
    Параметры:
        instance - ссылка на экземпляр класса peewee
            attr_name - имя поля
            role - флаг роли Qt (DisplayRole - отображение, EditRole - редактирование)
            special_font - специальный шрифт QFont для выделения пустых значений
    """
    # Проверка, есть ли поле с именем attr_name в instance
    if instance is None or not isinstance(instance, BaseModel) or not hasattr(instance, attr_name):
        return None

    # Получим само значение
    _value = getattr(instance, attr_name)

    # Для пустых значений
    if _value is None:
        if role == QtCore.Qt.DisplayRole:
            return global_const.defaultNoneDisplayedText
        elif role == QtCore.Qt.FontRole:
            return special_font

    # Получим тип поля
    field = instance._meta.fields[attr_name]

    # Для редактирования данные передаются без изменений, кроме внешних ключей
    if role == QtCore.Qt.EditRole:
        # Для внешних ключей - пишем id
        if not _value is None and isinstance(field, peewee.ForeignKeyField):
            return _value.id
        return _value

    # Для отображения представляем данные в текстовом виде
    if role == QtCore.Qt.DisplayRole:
        # Для внешнего ключа возвращаем дефолтную функцию представления связанного элемента
        if isinstance(field, peewee.ForeignKeyField):
            return _value.representation()
        # Для Enum'ов
        if isinstance(field, IntEnumField):
            return str(_value)
        # Для Boolean
        if isinstance(field, peewee.BooleanField):
            if _value: return global_const.defaultTrueDisplayedText
            return global_const.defaultFalseDisplayedText
        # Для двоичных данных
        if isinstance(field, (peewee.BlobField, peewee.BitField)):
            return global_const.defaultBlobDisplayedText
        # Текст, Целые числа и числа с плавающей точкой возвращаем без изменений
        if isinstance(field, (peewee.CharField, peewee.TextField, peewee.IntegerField, peewee.FloatField)):
            return _value
        # Время переводим в QTime
        if isinstance(field, peewee.TimeField):
            return DateAndTime.time_to_QTime(_value)
        # Дату переводим в QDate
        if isinstance(field, peewee.DateField):
            return DateAndTime.date_to_QDate(_value)
        # Дату_время переводим в QDateTime
        if isinstance(field, peewee.DateTimeField):
            return DateAndTime.datetime_to_QDateTime(_value)


