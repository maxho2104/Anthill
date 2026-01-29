import os
from typing import Optional
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QWidget, QMainWindow, QMenu, QAction, QFileDialog
from Peewee.Utils.DBManager import db_manager
from Common.Settings import settings


class MainWindow(QMainWindow):
    """Основное окно приложения"""
    def __init__(self, parent:QWidget = None):
        super().__init__(parent=parent)

        # Actions
        self._close_action: Optional[QAction] = None

        self._create_menu()
        self._restore_settings()

    def showEvent(self, event):
        settings.restoreWidgetGeometry(self, 'Forms', 'MainWindow')
        event.accept()

    def closeEvent(self, event):
        self._disconnectFromDB()
        settings.saveWidgetGeometry(self, 'Forms', 'MainWindow')
        settings.save()
        event.accept()

    def _restore_settings(self):
        """Чтение и восстановление настроек"""
        if settings.load():
            db_path = settings.get('Main settings', 'Database path')
            if db_path is None or not os.path.exists(db_path):
                self._connect_to_db_action_triggered()
            else:
                self._connectToDB(db_path)


    def _create_menu(self):
        database_menu:QMenu = self.menuBar().addMenu('База данных')
        open_action:QAction = database_menu.addAction('Подключиться к БД')
        open_action.triggered.connect(self._connect_to_db_action_triggered)
        self._close_action = database_menu.addAction('Отключиться от БД')
        self._close_action.setEnabled(False)
        self._close_action.triggered.connect(self._disconnectFromDB)
        database_menu.addSeparator()
        create_action:QAction = database_menu.addAction('Создать новую БД')
        create_action.triggered.connect(self._create_db_action_triggered)

    @pyqtSlot()
    def _connect_to_db_action_triggered(self):
        db_path = self._getDBPath()
        self._connectToDB(db_path)

    @pyqtSlot()
    def _create_db_action_triggered(self):
        db_path = self._getDBPath(True)
        if not db_path is None and len(db_path) > 0:
            self._disconnectFromDB()
            self._createDB(db_path)

    def _connectToDB(self, path: str) -> bool:
        """Подключение к БД, находящейся  в файле path"""
        if len(path) == 0:
            return False
        self._disconnectFromDB()
        if db_manager.connectDB(os.path.relpath(path)):
            settings.set(os.path.relpath(db_manager.db_path), 'Main settings', 'Database path')
            self._close_action.setEnabled(True)
        return db_manager.connected

    def _createDB(self, path:str) -> bool:
        """Создание новой БД"""
        if len(path) == 0: return False
        if db_manager.connected:
            self._disconnectFromDB()
        if not db_manager.connectDB(path): return False
        if not db_manager.createTables(): return False
        settings.set(os.path.relpath(db_manager.db_path), 'Main settings', 'Database path')
        return True

    def _getDBPath(self, create:bool=False) -> str:
        """Получение пути к БД, путем вызова диалога"""
        if not create:
            db_path = QFileDialog.getOpenFileName(self, caption='Открыть файл базы данных', directory='../',
                                                  filter='Файлы SQLite (*.db; *.sqlite; *.sqlite3; *.db3)')[0]
        else:
            db_path = QFileDialog.getSaveFileName(self, caption='Создать файл базы данных', directory='../',
                                                  filter='Файлы SQLite (*.db; *.sqlite; *.sqlite3; *.db3)')[0]
        return db_path

    @pyqtSlot()
    def _disconnectFromDB(self):
        """Отключение от БД"""
        if db_manager.connected:
            closed = db_manager.closeDB()
            self._close_action.setEnabled(not closed)