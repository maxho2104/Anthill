from typing import List
from pathlib import Path
from peewee import InternalError
from Peewee.Common.BaseModel import db, BaseModel
from Peewee.Classes import MainClasses
from Peewee.Classes.Content import Content

class DBManager:
    def __init__(self):
        self.db_path: str = ''
        self.connected: bool = False
        self.classes_to_creating:List[BaseModel] = [
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

    def is_connected(self) -> bool:
        """Проверяет, подключена ли база данных"""
        return self.connected and not db.is_closed()

    def connectDB(self, path: str) -> bool:
        """Подключение к существующей базе данных"""
        try:
            if self.is_connected():
                self.closeDB()
            self.db_path = path
            db.init(self.db_path)
            db.connect()
            self.connected = True
            print(f'База данных из файла {self.db_path} подключена')
            return True
        except InternalError as px:
            print(f"Ошибка подключения: {str(px)}")
            self.connected = False
            return False

    def createDB(self, path: str, clear_bd: bool = False) -> bool:
        """Создание новой базы данных"""
        if clear_bd and Path(path).exists():
            try:
                Path(path).unlink()
            except PermissionError as e:
                print(f'Невозможно очистить БД {path}!')
                return False

        if not self.connectDB(path):
            return False

        return self.createTables()

    def createTables(self) -> bool:
        """Создание таблиц в базе данных"""
        if not self.is_connected():
            print("Нет подключения к БД!")
            return False

        try:
            db.create_tables(self.classes_to_creating, safe=True)
            print('Структура таблиц создана...')
            return True
        except InternalError as px:
            print(f"Ошибка создания таблиц: {str(px)}")
            return False

    def closeDB(self) -> bool:
        """Закрытие соединения с базой данных"""
        try:
            if self.is_connected():
                self.connected = db.close()
                print('База данных отключена...')
            return True
        except Exception as e:
            print(f"Ошибка при закрытии БД: {str(e)}")
            return False

db_manager = DBManager()