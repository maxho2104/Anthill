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

def _handle_none_value(role: int, special_font: Optional[QtGui.QFont]) -> Any:
    if role == QtCore.Qt.DisplayRole:
        return global_const.defaultNoneDisplayedText
    elif role == QtCore.Qt.EditRole:
        return None
    elif role == QtCore.Qt.FontRole and special_font is not None:
        return special_font
    elif role == QtCore.Qt.ToolTipRole:
        return global_const.defaultNoneDisplayedText
    return QtCore.QVariant()


def _handle_field_value(field: Any, _value: Any, role: int, special_font: Optional[QtGui.QFont]) -> Any:
    if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
        return _handle_display_or_edit_role(field, _value, role)
    elif role == QtCore.Qt.FontRole:
        return _handle_font_role(_value, special_font)
    elif role == QtCore.Qt.ToolTipRole:
        return _handle_tooltip_role(_value)
    return QtCore.QVariant()


def _handle_display_or_edit_role(field: Any, _value: Any, role: int) -> Any:
    if role == QtCore.Qt.DisplayRole:
        if isinstance(field, peewee.ForeignKeyField):
            return _value.representation()
        elif isinstance(field, peewee.BooleanField):
            return global_const.defaultTrueDisplayedText if _value else global_const.defaultFalseDisplayedText
        elif isinstance(field, IntEnumField):
            return str(_value)
        elif isinstance(field, peewee.TimeField):
            return DateAndTime.time_to_QTime(_value)
        elif isinstance(field, peewee.DateField):
            return DateAndTime.date_to_QDate(_value)
        elif isinstance(field, peewee.DateTimeField):
            return DateAndTime.datetime_to_QDateTime(_value)
        elif isinstance(field, peewee.ManyToManyField):
            return [str(element.representation()) for element in _value].join(', ')
    return _value

def _handle_font_role(_value: Any, special_font: Optional[QtGui.QFont]) -> Any:
    if _value is None and special_font is not None:
        return special_font
    return QtCore.QVariant()


def _handle_tooltip_role(_value: Any) -> Any:
    return str(_value) if _value is not None else global_const.defaultNoneDisplayedText

def model_data_from_instance(instance: BaseModel, attr_name: str, role: int = QtCore.Qt.DisplayRole, special_font: Optional[QtGui.QFont] = None) -> Any:
    """Получение данных для модели Qt из экземпляра класса peewee по соответсвующего имени поля
    Параметры:
        instance - ссылка на экземпляр класса peewee
            attr_name - имя поля
            role - флаг роли Qt (DisplayRole - отображение, EditRole - редактирование)
            special_font - специальный шрифт QFont для выделения пустых значений
    """
    # Проверка, есть ли поле с именем attr_name в instance
    if instance is None or not isinstance(instance, BaseModel):
        return QtCore.QVariant()

    # Safely get the attribute value, handling potential exceptions from invalid FK references
    try:
        _value = getattr(instance, attr_name, None)
    except (peewee.DoesNotExist, AttributeError, TypeError):
        # If getting the attribute fails (e.g., due to invalid FK), return appropriate default
        if role == QtCore.Qt.DisplayRole:
            return global_const.defaultNoneDisplayedText
        else:
            return QtCore.QVariant()

    if _value is None:
        return _handle_none_value(role, special_font)

    field = instance._meta.fields.get(attr_name)
    if field is None:
        return QtCore.QVariant()

    return _handle_field_value(field, _value, role, special_font)
