from PyQt5 import QtWidgets
from typing import Union, Optional

"""Общие функции (чтобы не перегружать код)"""

def find_action_or_menu(menu: Union[QtWidgets.QMenuBar, QtWidgets.QMenu] , name: str) \
        -> Optional[Union[QtWidgets.QMenu, QtWidgets.QAction]]:
    """Рекурсивный поиск в меню по названию"""
    if not isinstance(menu, (QtWidgets.QMenuBar, QtWidgets.QMenu)):
        return None
    for item in menu.children():
        if isinstance(item, (QtWidgets.QMenu, QtWidgets.QAction)):
            if isinstance(item, QtWidgets.QMenu):
                text = item.title()
                if text == name:
                    return item
                find = find_action_or_menu(item, name)
                if not find is None:
                    return find
            else:
                text = item.text()
                if text == name:
                    return item
    return None

def get_db_path_from_dialog(parent:QtWidgets.QWidget, create:bool=False) -> str:
    """Получение пути к БД из диалога"""
    if not create:
        db_path = QtWidgets.QFileDialog.getOpenFileName(parent, caption='Открыть файл базы данных', directory='./',
                                                            filter='Файлы SQLite (*.db; *.sqlite; *.sqlite3; *.db3)')[0]
    else:
        db_path = QtWidgets.QFileDialog.getSaveFileName(parent, caption='Создать файл базы данных', directory='./',
                                                            filter='Файлы SQLite (*.db; *.sqlite; *.sqlite3; *.db3)')[0]
    return db_path