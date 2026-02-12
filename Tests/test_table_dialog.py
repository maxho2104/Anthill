import sys
import os
# Добавляем родительскую директорию в путь поиска модулей (для VSCode)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import peewee
import enum
import datetime
from typing import Any
from PyQt5 import QtWidgets
from framework import BaseModel, IntEnumField, StrExplainableIntEnum, DBManager, Settings, TableDialog

#------------------------------------------Тестовые классы--------------------------------------------------------------
class Person(BaseModel):
    """Человек с Ф.И.О."""
    last_name = peewee.CharField(verbose_name="Фамилия")
    first_name = peewee.CharField(verbose_name="Имя", null=True)
    second_name = peewee.CharField(verbose_name="Отчество", null=True)

    def representation(self) -> Any:
        res: str = str(self.last_name)
        if not self.first_name is None and len(str(self.first_name).strip()) > 0:
            res += f" {str(self.first_name).strip().title()[0]}."
            if not self.second_name is None and len(str(self.second_name).strip()) > 0:
                res += f" {str(self.second_name).strip().title()[0]}."
        return res

@enum.unique
class SubjectiveRatingEnum(StrExplainableIntEnum):
    NonSatisfactory = 2
    Satisfactory = 3
    Good = 4
    Excellent = 5

    @classmethod
    def _get_explanation_dict(cls):
        return {
            2: ("неуд.", "неудовлетворительно"),
            3: ("уд.", "удовлетворительно"),
            4: ("хор.", "хорошо"),
            5: ("отл.", "отлично"),
        }

class TestTable(BaseModel):
    """Тестовая таблица"""
    char_field = peewee.CharField(verbose_name="Текст(CharField)")
    text_field = peewee.TextField(verbose_name="Текст(TextField)", null=True)
    boolean_field = peewee.BooleanField(verbose_name="Двоичное поле", null=True)
    integer_field = peewee.IntegerField(verbose_name="Целочисленное поле", null=True)
    float_field = peewee.FloatField(verbose_name="Поле с плав. точкой", null=True)
    datetime_field = peewee.DateTimeField(verbose_name="Поле даты и времени", null=True)
    date_field = peewee.DateField(verbose_name="Поле даты", null=True)
    time_field = peewee.TimeField(verbose_name="Поле времени", null=True)
    foreign_key_field = peewee.ForeignKeyField(Person, backref="persons", verbose_name="Внешний ключ", null=True)
    int_enum_field = IntEnumField(SubjectiveRatingEnum, verbose_name="Поле перечислений", null=True)
#-----------------------------------------------------------------------------------------------------------------------
def use_PyQt5()->int:

    dialog = TableDialog(TestTable)
    dialog.show()
    return app.exec_()



if __name__ == "__main__":
    """Здесь запускается тест"""
    # Создаем приложения Qt
    app = QtWidgets.QApplication([])

    # Инициализируем настройки
    Settings('settings.json')
    Settings().load()

    # Указываем классы БД, с которыми хотим работать
    DBManager([Person, TestTable])
    # Подключаем базу
    DBManager().connectDB("..\\test_widget.db")
    # Если подключились и таблиц в БД нет - создаем и заполняем
    if DBManager().connected and not Person.table_exists():
        Person.create_table(True)
        Person.create(last_name="Иванов", first_name="Иван", second_name="Иванович")
        Person.create(last_name="Петров", first_name="Петр", second_name="Петрович")
        Person.create(last_name="Сидоров", first_name="Сидор", second_name="Сидорович")
    if DBManager().connected and not TestTable.table_exists():
        TestTable.create_table(True)
        TestTable.create(char_field="1-я запись", text_field="ТЕКСТ")
        TestTable.create(char_field="2-я запись", boolean_field=True)
        TestTable.create(char_field="3-я запись", integer_field=100)
        TestTable.create(char_field="4-я запись", float_field=50.5)
        TestTable.create(char_field="5-я запись", datetime_field=datetime.datetime.now())
        TestTable.create(char_field="6-я запись", date_field=datetime.date.today())
        TestTable.create(char_field="7-я запись", time_field=datetime.datetime.now().time())
        TestTable.create(char_field="8-я запись", foreign_key_field=Person.get_by_id(1))
        TestTable.create(char_field="9-я запись", int_enum_field=SubjectiveRatingEnum.Excellent)

    ret_code = use_PyQt5()

    # Отключаемся от базы
    DBManager().closeDB()
    # Сохраняем настройки
    Settings().save()

    sys.exit(ret_code)
