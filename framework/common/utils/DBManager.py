from PyQt5.QtCore import QObject, pyqtSignal
from pathlib import Path
from typing import Optional, Type, List, Iterable
from peewee import SqliteDatabase, InternalError
from ..decorators.Singleton import singleton
from ...peewee.classes.BaseModel import BaseModel

@singleton # работает как синглтон и
class DBManager(QObject):
    """Класс обеспечивает подключение/отключение от SQLITE БД,  создание таблиц"""
    connection_toggled = pyqtSignal(bool)
    def __init__(self, classes:Optional[Iterable[Type[BaseModel]]]=None, path:Optional[str]=None, parent:QObject = None):
        super().__init__(parent)
        self.db = SqliteDatabase(None)
        self.db_path: Optional[str] = None
        if not path is None:
            self.db_path = path
        self.connected: bool = False
        self.peewee_classes:Optional[List[Type[BaseModel]]] = None
        if not classes is None:
            self.setClasses(classes)


    def setClasses(self, classes:Iterable[Type[BaseModel]]):
        self.peewee_classes = list(classes)
        self.peewee_classes = list(classes)
        for peewee_class in self.peewee_classes:
            if issubclass(peewee_class, BaseModel):
                peewee_class.set_database(self.db)

    def connectDB(self, path: Optional[str]=None) -> bool:
        """Подключение к базе"""
        try:
            # Подключение
            if not path is None:
                self.db_path = path
            self.db.init(self.db_path)
            self.connected = True
            print(f'База данных из файла {self.db_path} подключена')
            self.connection_toggled.emit(self.connected)
            return True
        except InternalError as px:
            print(str(px))
        return False

    def closeDB(self)->bool:
        """Отключение от базы"""
        if not self.connected:
            print('База не была подключена')
            return True
        if not self.db.close():
            print(f'База данных {self.db_path} отключена...')
            self.connected = False
            self.connection_toggled.emit(self.connected)
            return True
        print(f'Попытка отключения от БД не удалась')
        return False

    def createDB(self, path: str, clear_bd: bool = False) -> bool:
        """Создание новой базы"""
        # Отключение уже подключенной базы
        if not self.closeDB():
            return False
        if clear_bd:
            path = Path(path)
            if path.exists():
                try:
                    path.unlink()
                except PermissionError as e:
                    print(f'Невозможно очистить БД {path}!')
                    return False
        if not self.connectDB(path):
            return False
        try:
            # Создание таблиц
            if self.createTables():
                return True
        except InternalError as px:
            print(str(px))
            self.closeDB()
        return False

    def createTables(self) -> bool:
        if len(self.peewee_classes) == 0 or not self.connected:
            return False
        try:
            self.db.create_tables(self.peewee_classes)
            print('Структура таблиц создана...')
        except InternalError as px:
            print(str(px))
            return False
        return True
