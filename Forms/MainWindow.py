import os
from PyQt5 import QtCore, QtWidgets
from framework import DBManager
from framework import Settings
from Peewee.Classes.MainClasses import *
from Peewee.Classes.Content import *
from common_functions import functions


class MainWindow(QtWidgets.QMainWindow):
    """Основная форма приложения"""

    def showEvent(self, event):
        """Действия при открытии окна"""
        Settings().restoreWidgetGeometry(self, 'Forms', 'MainWindow')
        event.accept()

    def closeEvent(self, event):
        """Действия при закрытии окна"""
        DBManager().closeDB()
        Settings().saveWidgetGeometry(self, 'Forms', 'MainWindow')
        Settings().save()
        event.accept()

    def __init__(self, parent:QtWidgets.QWidget=None):
        super().__init__(parent)
        # Перечисляем таблицы, с которыми будет работать программа
        working_tables = [
            Rank,
            ProcessUnit,
            Department,
            WorkingGroup,
            Employee,
            Task,
            Rater,
            Rating,
            RatingList,
            Attachment,
            File,
            Content
        ]
        self.make_ui()
        # Инициализация и загрузка настроек
        Settings('.\\settings.json')
        Settings().load()
        # Инициализация БД
        DBManager(classes=working_tables)
        DBManager().connection_toggled.connect(self.on_db_connection_toggled)
        # Загрузка БД, сохраненной в настройках (если есть)
        db_path = Settings().get('Main settings', 'Database path')
        if (not db_path is None) and os.path.exists(db_path):
            DBManager().connectDB(db_path)

    def make_ui(self):
        """Создание интерфейса"""
        self.make_menu()
        tab_widget = QtWidgets.QTabWidget()
        tab_widget.setTabPosition(QtWidgets.QTabWidget.West)
        content_tab = tab_widget.addTab(QtWidgets.QWidget(), 'Материалы')

        self.setCentralWidget(tab_widget)



    def make_menu(self):
        """Создание меню"""
        menu_bar = QtWidgets.QMenuBar()
        database_menu = menu_bar.addMenu('База данных')
        connect_action = database_menu.addAction('Подключить БД')
        connect_action.triggered.connect(lambda: self.connect_to_database())
        disconnect_action = database_menu.addAction('Отключить БД')
        disconnect_action.triggered.connect(lambda: DBManager().closeDB())
        disconnect_action.setEnabled(DBManager().connected)
        database_menu.addSeparator()
        create_db_action = database_menu.addAction('Создать новую БД')
        create_db_action.triggered.connect(lambda: self.connect_to_database(True))
        self.setMenuBar(menu_bar)

    def connect_to_database(self, create:bool=False):
        db_path = functions.get_db_path_from_dialog(self,create)
        if len(db_path)>0:
            if create:
                DBManager().createDB(db_path)
            else:
                if os.path.exists(db_path):
                    DBManager().connectDB(db_path)
            if DBManager().connected:
                Settings().set(os.path.relpath(db_path), 'Main settings', 'Database path')

    @QtCore.pyqtSlot(bool)
    def on_db_connection_toggled(self, connected:bool):
        """Действия при подключении/отключении БД"""
        functions.find_action_or_menu(self.menuBar(), 'Отключить БД').setEnabled(connected)



