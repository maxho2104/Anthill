from pathlib import Path
from peewee import InternalError
from Peewee.Common.BaseModel import db
from Peewee.Classes import MainClasses
from Peewee.Classes.Content import Content

class DBManager:
    def __init__(self):
        self.db_path: str = ''
        self.connected: bool = False
        self.classes_to_creating = [
            MainClasses.ProcessUnit,
            MainClasses.Department,
            MainClasses.WorkingGroup,
            MainClasses.Employee,
            MainClasses.Rater,
            MainClasses.File,
            MainClasses.RatingList,
            MainClasses.Rating,
            MainClasses.Task,
            Content
        ]

    def connectDB(self, path: str) -> bool:
        try:
            # Подключение
            self.db_path = path
            db.init(path)
            self.connected = True
            print(f'База данных из файла {self.db_path} подключена')
            return True
        except InternalError as px:
            print(str(px))
        return False

    def createDB(self, path: str, clear_bd: bool = False) -> bool:
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
        if not self.connected:
            return False
        try:
            db.create_tables(self.classes_to_creating)
            print('Структура таблиц создана...')
        except InternalError as px:
            print(str(px))
            return False
        return True

    def closeDB(self)->bool:
        closed = not db.close()
        if closed:
            print('База данных отключена...')
            self.connected = False
        return closed

db_manager = DBManager()