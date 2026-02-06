from enum import unique
from peewee import CharField, DateField, FloatField, IntegerField, ForeignKeyField
from framework import StrExplainableIntEnum, BaseModel, IntEnumField, StrExplainableIntEnum
from Peewee.Classes.MainClasses import Task, ProcessUnit, Department, Employee, WorkingGroup, Rater, Rating, File


@unique
class ContentType(StrExplainableIntEnum):
    """Тип материала(информационно-отчетного документа)"""
    message     = 0
    document    = 1
    reference   = 2
    sample      = 3
    identity    = 4

    @classmethod
    def _get_explanation_dict(cls):
        return {
            0:  ('Д',  'Доклад'),
            1:  ('О',  'Отчет'),
            2:  ('С',  'Справка'),
            3:  ('Об', 'Образец продукции'),
            4:  ('ТД', 'Техническая документация'),
        }

class Content(BaseModel):
    """Материал (документ)"""
    type = IntEnumField(ContentType, verbose_name='Тип материала')
    doc_number = CharField(verbose_name='Исходящий номер')
    doc_date = DateField(verbose_name='Дата отправки')
    name = CharField(verbose_name='Название')
    task = ForeignKeyField(Task, backref='tasks', verbose_name='Задача')
    incoming_doc_number = CharField(verbose_name='Входящий номер', null=True)
    incoming_doc_date = DateField(verbose_name='Дата получения', null=True)
    comment = CharField(verbose_name='Примечание', null=True)
    sender = ForeignKeyField(ProcessUnit, backref='senders', verbose_name='Отправитель')
    department = ForeignKeyField(Department, backref='departments', verbose_name='Подразделение')
    employee = ForeignKeyField(Employee, backref='employees', verbose_name='Исполнитель', null=True)
    working_group = ForeignKeyField(WorkingGroup, backref='working_groups', verbose_name='РГ', null=True)
    rater = ForeignKeyField(Rater, backref='raters', verbose_name='Оценивающий')
    primary_rating = ForeignKeyField(Rating, backref='primary_ratings', verbose_name='Предварительная оценка', null=True)
    rating = ForeignKeyField(Rating, backref='ratings', verbose_name='Окончательная оценка', null=True)
    cost = FloatField(verbose_name='Стоимость', null=True)               # Для образца продукции
    serial_number = CharField(verbose_name='Заводской номер', null=True) # Для образца продукции или тех. документации
    produce_year = IntegerField(verbose_name='Год выпуска', null=True)   # Для образца продукции или тех. документации

class Attachment(BaseModel):
    """Приложения (техническая таблица для связи многие ко многим: к материалу могут прилагаться несколько файлов)"""
    content = ForeignKeyField(Content, backref='contents', verbose_name='Материал', null=True)
    file = ForeignKeyField(File, backref='files', verbose_name='Файл')