from typing import Optional, Type, Any, List
import peewee
from sys import float_info
from PyQt5 import QtWidgets, QtCore
import datetime
from typing import Type
from ...common import DateAndTime, WidgetFunctions

from PyQt5.QtWidgets import QComboBox
from ... import global_const
from ..classes import BaseModel, IntEnumField

def get_field_name(field:Type[peewee.Field])->str:
    """Возвращает русскоязычное название поля (если есть, иначе - просто название поля)"""
    name = field.name
    if not field.verbose_name is None and len(field.verbose_name.strip()) > 0:
        name = field.verbose_name
    return name

class ItemWidget(QtWidgets.QWidget):
    """Виджет для редактирования полей записи БД (peewee)"""
    class ItemWidgetElement(QtWidgets.QWidget):
        """Элемент виджета"""
        def __init__(self, field:Type[peewee.Field], parent:QtWidgets.QWidget=None):
            super().__init__(parent)
            self.editor = None
            self.field = field
            self.none_checkbox = None
            self.make_ui()
            self.last_error_str = None

        def make_ui(self):
            main_layout = QtWidgets.QHBoxLayout()
            main_layout.setContentsMargins(0,0,0,0)
            # Создание визуального компонента, в зависимости от типа поля
                # Текст (CharField)
            if isinstance(self.field, peewee.CharField):
                self.editor = QtWidgets.QLineEdit()
                self.editor.setMaxLength(self.field.max_length)
                self.editor.setPlaceholderText(global_const.defaultNoneDisplayedText)
                # Текст (TextField)
            elif isinstance(self.field, peewee.TextField):
                self.editor = QtWidgets.QTextEdit()
                self.editor.setPlaceholderText(global_const.defaultNoneDisplayedText)
                # Enum'ы, внешние ключи, двоичные данные
            elif isinstance(self.field, (IntEnumField, peewee.ForeignKeyField, peewee.BooleanField)):
                self.editor = QComboBox()
                    # Enum'ы
                if isinstance(self.field, IntEnumField):
                    WidgetFunctions.fill_int_enum_combobox(self.field, self.editor)
                    # внешние ключи
                elif isinstance(self.field, peewee.ForeignKeyField):
                    WidgetFunctions.fill_foreign_combobox(self.field, self.editor)
                    # двоичные данные
                else:
                    WidgetFunctions.fill_boolean_combobox(self.field, self.editor)
            # Целые числа
            elif isinstance(self.field, peewee.IntegerField) and not (isinstance(self.field, IntEnumField)):
                self.editor = QtWidgets.QSpinBox()
                self.editor.setRange(-2000000000, 2000000000)
            # Числа с плавающей точкой
            elif isinstance(self.field, peewee.FloatField):
                self.editor = QtWidgets.QDoubleSpinBox()
                self.editor.setRange(float_info.min, float_info.max)
            # Дата
            elif isinstance(self.field, peewee.DateField):
                self.editor = QtWidgets.QDateEdit()
                WidgetFunctions.default_fill_date_edit(self.editor)
            # Время
            elif isinstance(self.field, peewee.TimeField):
                self.editor = QtWidgets.QTimeEdit()
                self.editor.setTime(QtCore.QTime.currentTime())
            # Дата/время
            elif isinstance(self.field, peewee.DateTimeField):
                self.editor = QtWidgets.QDateTimeEdit()
                #self.editor.setDisplayFormat('hh:mm dd.MM.yyyy')
                WidgetFunctions.default_fill_datetime_edit(self.editor)

            # Добавим self.editor в main_layout
            main_layout.addWidget(self.editor, 1)

            # Для нулевых значений добавим checkbox'ы
            if self.field.null and isinstance(self.editor, QtWidgets.QAbstractSpinBox):
                self.none_checkbox = QtWidgets.QCheckBox(global_const.defaultNoneDisplayedText)
                self.none_checkbox.setChecked(False)
                self.none_checkbox.toggled.connect(lambda checked: self.editor.setEnabled(not checked))
                main_layout.insertWidget(0, self.none_checkbox,0)
            self.setLayout(main_layout)

        def validate(self)->bool:
            """Проверка правильности заполнения элемента"""
            # Проверка заполнения LineEdit'ов и TextEdit'ов для обязательных полей
            field_caption = get_field_name(self.field)
            if not self.field.null:
                if isinstance(self.editor, (QtWidgets.QLineEdit, QtWidgets.QTextEdit)):
                    if isinstance(self.editor, QtWidgets.QLineEdit):
                        text = self.editor.text()
                    else:
                        text = self.editor.toPlainText()
                    if len(text) == 0:
                        # Заполним строку ошибки
                        self.last_error_str = f'Поле "{field_caption}" обязательно к заполнению!'
                        return False

            # Проверка заполнения редактируемых ComboBox'ов
            if isinstance(self.editor, QtWidgets.QComboBox) and self.editor.isEditable():
                if not self.editor.itemText(self.editor.currentIndex()) == self.editor.currentText():
                    self.last_error_str = f'Значение "{self.editor.currentText()}" для поля "{field_caption}" недопустимо!'
                    return False
            return True


        @property
        def value(self)->Any:
            """Получение значения элемента"""
            # Для QLineEdit'ов и QTextEdit'ов
            if isinstance(self.editor, (QtWidgets.QLineEdit, QtWidgets.QTextEdit)):
                if isinstance(self.editor,QtWidgets.QLineEdit):
                    text = self.editor.text()
                else:
                    text = self.editor.toPlainText()
                if self.field.null and len(text)==0:
                    return None
                return text
            # Для QComboBox'ов
            elif isinstance(self.editor, QtWidgets.QComboBox):
                return self.editor.currentData()
            # Для SpinBox'ов и эдитов даты/времени
            elif isinstance(self.editor, QtWidgets.QAbstractSpinBox):
                # Если прочеканы чекбоксы - возвращаем None
                if not self.none_checkbox is None and self.field.null:
                    if self.none_checkbox.isChecked():
                        return None
                    else:
                        # Возвращаем числа, дату и время (в зависимости от чекбокса)
                        if isinstance(self.editor, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
                            return self.editor.value()
                        elif isinstance(self.editor, QtWidgets.QDateEdit):
                            return DateAndTime.QDate_to_date(self.editor.date())
                        elif isinstance(self.editor, QtWidgets.QTimeEdit):
                            return DateAndTime.QTime_to_time(self.editor.time())
                        elif isinstance(self.editor, QtWidgets.QDateTimeEdit):
                            return DateAndTime.QDateTime_to_datetime(self.editor.dateTime())
            return None

        @value.setter
        def value(self, _val:Any):
            """Установка значения для элемента"""
            # Для пустых значений (если присутствует self.none_checkbox)
            if _val is None and (not self.none_checkbox is None):
                self.none_checkbox.setChecked(True)
                return
            # Для QLineEdit'ов и QTextEdit'ов
            if isinstance(self.editor, (QtWidgets.QLineEdit, QtWidgets.QTextEdit)):
                if _val is None:
                    self.editor.clear()
                else:
                    self.editor.setText(str(_val))
            # Для QComboBox'ов
            if isinstance(self.editor, QtWidgets.QComboBox):
                WidgetFunctions.set_combo_value(self.editor,_val)
            # Для чисел, даты и времени (в зависимости от чекбокса)
            if isinstance(self.editor, QtWidgets.QSpinBox):
                self.editor.setValue(int(_val))
            elif isinstance(self.editor, QtWidgets.QDoubleSpinBox):
                self.editor.setValue(float(_val))
            elif isinstance(self.editor, QtWidgets.QDateEdit) and isinstance(_val, datetime.date):
                self.editor.setDate(DateAndTime.date_to_QDate(_val))
            elif isinstance(self.editor, QtWidgets.QTimeEdit) and isinstance(_val, datetime.time):
                self.editor.setTime(DateAndTime.time_to_QTime(_val))
            elif isinstance(self.editor, QtWidgets.QDateTimeEdit) and isinstance(_val, datetime.datetime):
                self.editor.setDateTime(DateAndTime.datetime_to_QDateTime(_val))

    def __init__(self, peewee_class:Type[BaseModel], parent:QtWidgets.QWidget=None):
        super().__init__(parent)
        self.peewee_class = peewee_class
        self.elements:List[ItemWidget.ItemWidgetElement] = []
        self.peewee_instance:Optional[peewee_class] = None
        layout = QtWidgets.QGridLayout()
        for field_name in list(peewee_class._meta.fields.keys())[1:]:
            # Создаем label и добавляем в layout
            caption = peewee_class._meta.fields[field_name].verbose_name
            if caption is None:
                caption = field_name
            # Для обязательных полей - label жирным шрифтом
            label = QtWidgets.QLabel()
            nullable = peewee_class._meta.fields[field_name].null
            if nullable:
                label.setText(f'{caption}:')
            else:
                label.setText(f'<b>{caption}:</b>')
                label.setTextFormat(QtCore.Qt.RichText)
            layout.addWidget(label, list(self.peewee_class._meta.fields).index(field_name), 0, QtCore.Qt.AlignRight)
            # Создаем элемент и добавляем в список элементов и в layout
            element = self.ItemWidgetElement(self.peewee_class._meta.fields[field_name])
            self.elements.append(element)
            layout.addWidget(element, list(self.peewee_class._meta.fields).index(field_name), 1)

            label.setBuddy(element)

            # Применяем layout
            self.setLayout(layout)

    def set_object(self, peewee_instance:BaseModel):
        """Установка записи БД для отображения и редактирования"""
        if not isinstance(peewee_instance, self.peewee_class): return
        self.peewee_instance = peewee_instance
        for element in self.elements:
            field_name = element.field.name
            if hasattr(self.peewee_instance, field_name):
                element.value = getattr(self.peewee_instance, field_name)

    def set_values_to_object(self):
        """Сохранение значений элементов для текущей записи БД"""
        if self.peewee_instance is None: return
        for element in self.elements:
            field_name = element.field.name
            if hasattr(self.peewee_instance, field_name):
                 setattr(self.peewee_instance, field_name, element.value)

    def check_input(self)->bool:
        """Проверка правильности ввода"""
        for element in self.elements:
            if not element.validate():
                if self.parent() is None:
                    parent = self
                else:
                    parent = self.parent()
                QtWidgets.QMessageBox.warning(parent, 'Внимание!', element.last_error_str)
                element.editor.setFocus()
                return False
        return True




class ItemDialog(QtWidgets.QDialog):
    """Диалог для редактирования полей записи БД (peewee)"""
    def __init__(self, peewee_class:Type[BaseModel], parent:QtWidgets.QWidget=None):
        super().__init__(parent=parent)
        self.peewee_class = peewee_class
        main_layout = QtWidgets.QVBoxLayout()
        # Создадим ItemWidget и добавим его в layout
        self.item_widget = ItemWidget(self.peewee_class)
        main_layout.addWidget(self.item_widget,1)
        # Создадим кнопки, добавим их в layout и назначим обработчики (названия кнопок не менять, завязаны на стиль!)
        button_layout = QtWidgets.QHBoxLayout()
        self.OkButton = QtWidgets.QPushButton('Ок')
        self.OkButton.clicked.connect(self.onOkButtonClicked)
        button_layout.addWidget(self.OkButton)
        self.CancelButton = QtWidgets.QPushButton('Отмена')
        self.CancelButton.clicked.connect(self.reject)
        button_layout.addWidget(self.CancelButton)
        main_layout.addLayout(button_layout,0)
        self.setLayout(main_layout)

    @QtCore.pyqtSlot()
    def onOkButtonClicked(self):
        """Обработчик нажатия кнопки 'Ок'"""
        if not self.item_widget.check_input():
            return
        self.item_widget.set_values_to_object()
        self.accept()

    @staticmethod
    def createObject(peewee_class: Type[BaseModel], parent: QtWidgets.QWidget = None):
        """Создание нового объекта (записи БД) класса peewee"""
        dialog = ItemDialog(peewee_class, parent=parent)
        peewee_object = peewee_class()
        dialog.item_widget.set_object(peewee_object)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            return peewee_object
        return None

    @staticmethod
    def editObject(peewee_object: BaseModel, parent: QtWidgets.QWidget = None):
        """Редактирование существующего объекта (записи БД) класса peewee"""
        if not isinstance(peewee_object, BaseModel): return None
        dialog = ItemDialog(type(peewee_object), parent)
        dialog.item_widget.set_object(peewee_object)
        if dialog.exec() == QtWidgets.QDialog.Accepted:
            return peewee_object
        return None



    
