from typing import Optional, Any, Dict
from peewee import Database, Model, DoesNotExist, CharField, TextField, DateTimeField, ForeignKeyField


class BaseModel(Model):
    """Базовый класс для всех классов ОРМ"""
    class Meta:
        database: Optional[Database] = None

    @classmethod
    def set_database(cls, db:Database, **kwargs):
        cls._meta.database = db

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

    def to_dict_simple(self):
        """Convert model instance to dictionary"""
        return {field.name: getattr(self, field.name) for field in self._meta.fields.values()}

    def to_dict(self) -> Dict[str, Any]:
        """Преобразование модели в словарь"""
        data:Dict[str, Any] = {}
        for field_name in self._meta.fields.keys():
            value = getattr(self, field_name)
            field_type = self._meta.fields[field_name]

            if value is None:
                continue
            if isinstance(field_type, CharField):
                data[field_name] = str(value)
            elif isinstance(field_type, TextField):
                data[field_name] = str(value)
            elif isinstance(field_type, DateTimeField):
                data[field_name] = value.strftime('%d.%m.%Y')
            elif isinstance(field_type, ForeignKeyField):
                data[field_name] = value.id
            else:
                data[field_name] = value
        return data