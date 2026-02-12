from typing import Any
from peewee import CharField, DateField, ForeignKeyField
from enum import unique
from framework import BaseModel, IntEnumField, global_const, StrExplainableIntEnum


class Rank(BaseModel):
    """Научное звание сотрудника (если есть)"""
    name = CharField(verbose_name='Наименование')
    short = CharField(verbose_name='Сокращенное наименование', null=True)

    def representation(self) -> Any:
        if self.short is not None and len(str(self.short).strip()) > 0:
            return str(self.short)
        return str(self.name)

class ProcessUnit(BaseModel):
    """Филиал предприятия"""
    number = CharField(verbose_name='Условный номер')
    name = CharField(verbose_name='Полное наименование', null=True)
    short = CharField(verbose_name='Сокращенное наименование', null=True)

    def representation(self) -> Any:
        if self.short is not None and len(str(self.short).strip()) > 0:
            return str(self.short)
        return str(self.number)

class Department(BaseModel):
    """Подразделение (отдел) предприятия"""
    name = CharField(verbose_name='Название')
    short = CharField(verbose_name='Сокращенное название')
    process_unit = ForeignKeyField(ProcessUnit, backref='units', verbose_name='Филиал')

    def representation(self) -> Any:
        return f'{self.short} {self.process_unit.representation()}'

class WorkingGroup(BaseModel):
    """Рабочая группа"""
    name = CharField(verbose_name='Наименование')
    department = ForeignKeyField(Department, backref='departments', verbose_name='Подразделение')
    comment = CharField(verbose_name='Примечание', null=True)

class Employee(BaseModel):
    """Сотрудник"""
    last_name = CharField(verbose_name='Фамилия')
    first_name = CharField(verbose_name='Имя')
    second_name = CharField(verbose_name='Отчество', null=True)
    rank = ForeignKeyField(Rank, backref='ranks', verbose_name='Научное звание', null=True)
    department = ForeignKeyField(Department, backref='departments', verbose_name='Подразделение', null=True)
    post = CharField(verbose_name='Должность', null=True)
    working_group = ForeignKeyField(WorkingGroup, backref='working_groups', verbose_name='В составе рабочей группы', null=True)
    working_group_post = CharField(verbose_name='Должность в рабочей группы', null=True)
    working_group_start = DateField(verbose_name='Дата начала деятельности в РГ', null=True)
    working_group_end = DateField(verbose_name='Дата окончания деятельности в РГ', null=True)

    def representation(self) -> Any:
        """Дефолтное представление сотрудника в виде записи типа: 'Иванов И.И.'"""
        res = ''
        # Запишем фамилию
        if self.last_name is not None: # Вдруг фамилию не знают
            res += str(self.last_name).strip().title()
        # Добавим инициал имени (или все имя, если нет фамилии)
        if self.first_name is not None and len(str(self.first_name).strip()):
            if len(res)>0:
                res += f' {str(self.first_name).strip().title()[0]}.'
            else:
                res +=str(self.first_name).strip().title()
        # Добавим инициал отчества (или все отчество, если нет фамилии)
        if self.second_name is not None and len(str(self.second_name).strip()):
            if self.last_name is None or len(str(self.last_name).strip()) == 0:
                if len(res)>0:
                    res += ' '
                res += str(self.second_name).strip().title()
            else:
                res += f' {str(self.second_name).strip().title()[0]}.'
        return res

class Rater(BaseModel):
    """Организация (подразделение), производящая оценку материала"""
    number = CharField(verbose_name='Условный номер')
    name = CharField(verbose_name='Название', null=True)
    short = CharField(verbose_name='Сокращенное название', null=True)

    def representation(self) -> Any:
        if not self.short is None and len(self.short) > 0:
            return self.short
        return super().representation()

class File(BaseModel):
    """Файл"""
    name = CharField(verbose_name='Имя файла')
    type = CharField(verbose_name='Формат файла')
    storagePath = CharField(verbose_name='Относительный путь к файлу в хранилище', null=True)

class RatingList(BaseModel):
    """Список (документ) с оценками"""
    number = CharField(verbose_name='Номер документа')
    date = DateField(verbose_name='Дата отправки документа', formats=global_const.correct_dates)

    def representation(self) -> Any:
        """Представление в виде '12/3456... от 01.04.2025'"""
        res = 'б/н'
        if self.number is not None and len(str(self.number).strip()) > 0:
            res = str(self.number).strip()
        if self.date is not None:
            res += f' от {self.date.strftime("%d.%m.%Y")}'
        return res

@unique
class RatingValue(StrExplainableIntEnum):
    """Тип оценки материала (документа)"""
    not_interesting = 0
    interesting     = 1
    valuable        = 2
    important       = 3

    @classmethod
    def _get_explanation_dict(cls):
        return {
            0: ('Неуд.', 'Неудовлетворительно'),
            1: ('Уд.',   'Удовлетворительно'),
            2: ('Хор.',  'Хорошо'),
            3: ('Отл.',  'Отлично')
        }

class Rating(BaseModel):
    """Оценка материала (документа)"""
    value = IntEnumField(RatingValue, verbose_name='Оценка')
    rating_list = ForeignKeyField(RatingList, verbose_name='Основание', backref='rating_lists', null=True)

    def representation(self) -> Any:
        if self.value is not None:
            return str(self.value)
        return None

@unique
class TaskType(StrExplainableIntEnum):
    """Тип задачи"""
    oz = 0
    dz = 1

    @classmethod
    def _get_explanation_dict(cls):
        return {
            0: ('ОЗ', 'Основная задача'),
            1: ('ДЗ', 'Дополнительная задача')
        }

class Task(BaseModel):
    """Задача"""
    code = CharField(verbose_name='Наименование')
    comment = CharField(verbose_name='Примечание')
    # Для хранения использовать значения перечисления TaskType
    type = IntEnumField(TaskType, verbose_name='Тип задачи')