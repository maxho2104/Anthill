from peewee import Database, SqliteDatabase, Model, TextField, CharField, DoesNotExist
from typing import Any

# Синглтон для операций с БД (открытие/закрытие, создание таблиц, должен вызываться только в контролирующем БД классе)
db = SqliteDatabase(None)

class BaseModel(Model):
    """Базовый класс для всех классов ОРМ"""
    class Meta:
        database: Database = db

    @classmethod
    def get_by_id(cls, _id):
        try:
            result = cls.get(cls._meta.primary_key == _id)
        except DoesNotExist:
            result = None
        return result

    def representation(self) -> Any:
        """Дефолтная функция представления данных класса (при необходимости следует переопределять в потомках)"""
        # Получаем имена полей без id
        columns = [key for key in self.__class__._meta.columns.keys()][1:]
        # Выбираем первое попавшееся текстовое поле
        representing_column = None
        for column in columns:
            if isinstance(self.__class__._meta.columns[column], (CharField, TextField)):
                representing_column = column
                break
        if representing_column:
            return getattr(self, representing_column)
        return getattr(self, 'id')