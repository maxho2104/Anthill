from builtins import isinstance
from typing import Type, Union
import datetime
from PyQt5 import QtWidgets, QtCore
import peewee
import sys

from PyQt5.QtWidgets import QComboBox

from ..classes import IntEnumField
from ...common import WidgetFunctions, DateAndTime

class SpinWidget(QtWidgets.QWidget):
    reset_clicked = QtCore.pyqtSignal()
    def __init__(self, field:Type[peewee.Field], parent=None):
        super().__init__(parent)
        self.field = field
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        if isinstance(self.field, peewee.IntegerField) and not isinstance(self.field, IntEnumField):
            self.editor = QtWidgets.QSpinBox(self)
            self.editor.setRange(-2000000000, 2000000000)
        elif isinstance(self.field, peewee.FloatField):
            self.editor = QtWidgets.QDoubleSpinBox(self)
            self.editor.setRange(sys.float_info.min, sys.float_info.max)
        elif isinstance(self.field, peewee.TimeField):
            self.editor = QtWidgets.QTimeEdit(self)
            self.editor.setTime(QtCore.QTime.currentTime())
        elif isinstance(self.field, peewee.DateField):
            self.editor = QtWidgets.QDateEdit(self)
            WidgetFunctions.default_fill_date_edit(self.editor)
        elif isinstance(self.field, peewee.DateTimeField):
            self.editor = QtWidgets.QDateTimeEdit(self)
            WidgetFunctions.default_fill_datetime_edit(self.editor)
        layout.addWidget(self.editor,1)
        self.reset_button = QtWidgets.QToolButton()
        self.reset_button.setText('❌')
        self.reset_button.setToolTip('Сброс')
        self.reset_button.clicked.connect(lambda :self.reset_clicked.emit())
        layout.addWidget(self.reset_button,0)
        self.setLayout(layout)

    def showEvent(self, a0):
        self.editor.selectAll()
        self.editor.setFocus()

    @property
    def value(self):
        if isinstance(self.editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
            return self.editor.value()
        elif isinstance(self.editor, QtWidgets.QTimeEdit):
            return DateAndTime.QTime_to_time(self.editor.time())
            #return self.editor.time()
        elif isinstance(self.editor, QtWidgets.QDateEdit):
            #return self.editor.date()
            return DateAndTime.QDate_to_date(self.editor.date())
        elif isinstance(self.editor, QtWidgets.QDateTimeEdit):
            return DateAndTime.QDateTime_to_datetime(self.editor.dateTime())
        return None

    @value.setter
    def value(self, value: Union[int, float, datetime.time, datetime.date, datetime.datetime]):
        if value is None:
            return
        if isinstance(self.editor, QtWidgets.QSpinBox) and isinstance(value, int):
            self.editor.setValue(value)
        elif isinstance(self.editor, QtWidgets.QDoubleSpinBox) and isinstance(value, (int, float)):
            self.editor.setValue(value)
        elif isinstance(self.editor, QtWidgets.QDateTimeEdit):
            if isinstance(self.editor, QtWidgets.QTimeEdit) and isinstance(value, datetime.time):
                self.editor.setTime(DateAndTime.time_to_QTime(value))
            elif isinstance(self.editor, QtWidgets.QDateEdit) and isinstance(value, datetime.date):
                self.editor.setDate(DateAndTime.date_to_QDate(value))
            else:
                self.editor.setDateTime(DateAndTime.datetime_to_QDateTime(value))


class TableDelegate(QtWidgets.QStyledItemDelegate):
    """Универсальный делегат для таблицы peewee"""
    def __init__(self, field:Type[peewee.Field], parent=None):
        super().__init__(parent)
        self.field = field

    def _set_none(self, index:QtCore.QModelIndex, editor: QtWidgets.QWidget):
        index.model().setData(index, None)
        self.closeEditor.emit(editor)

    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

    def createEditor(self, parent, option, index):
        editor:QtWidgets.QWidget = None
        if isinstance(self.field, (peewee.BooleanField, peewee.ForeignKeyField, IntEnumField)):
            editor = QComboBox(parent)
            if isinstance(self.field, peewee.BooleanField):
                WidgetFunctions.fill_boolean_combobox(self.field, editor)
            elif isinstance(self.field, peewee.ForeignKeyField):
                WidgetFunctions.fill_foreign_combobox(self.field, editor)
            else:
                WidgetFunctions.fill_int_enum_combobox(self.field, editor)
        elif isinstance(self.field, (peewee.IntegerField, peewee.FloatField, peewee.TimeField, peewee.DateField, peewee.DateTimeField)):
            editor = SpinWidget(self.field, parent)
            editor.reset_clicked.connect(lambda: self._set_none(index, editor))
        return editor

    def setEditorData(self, editor, index):
        if isinstance(editor, QtWidgets.QComboBox):
            WidgetFunctions.set_combo_value(editor, index.data(QtCore.Qt.EditRole))
            if editor.isEditable():
                editor.lineEdit().selectAll()
        elif isinstance(editor, SpinWidget):
            editor.value = index.data(QtCore.Qt.EditRole)

    def setModelData(self, editor, model, index):
        if isinstance(editor, QtWidgets.QComboBox):
            model.setData(index, editor.currentData(), QtCore.Qt.EditRole)
        elif isinstance(editor, SpinWidget):
            model.setData(index, editor.value, QtCore.Qt.EditRole)


