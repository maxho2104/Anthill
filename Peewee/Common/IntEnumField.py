from typing import Type
from enum import IntEnum
from peewee import IntegerField


class IntEnumField(IntegerField):
    """Класс для работы с целочисленными перечислениями типа IntEnum"""
    def __init__(self, enum_class: Type[IntEnum], **kwargs):
        super().__init__(**kwargs)
        self.enum_class = enum_class

    def db_value(self, value):
        # Преобразуем значение IntEnum в его целочисленное представление
        if isinstance(value, IntEnum):
            return value.value
        elif isinstance(value, int):
            return value
        elif value is None and self.null:
            return None
        else:
            raise ValueError(f'Недопустимое значение для поля {self.__name__}: {value}')

    def python_value(self, value):
        # Преобразуем значение из базы данных в соответствующее IntEnum
        if isinstance(value, int) and value in [c.value for c in self.enum_class]:
            return self.enum_class(value)
        elif self.null and value is None:
            return None
        else:
            raise ValueError(f'Недопустимое значение для поля {self.__name__}: {value}')