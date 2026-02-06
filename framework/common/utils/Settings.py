from ..decorators.Singleton import singleton
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import QWidget, QTableView, qApp, QStyle
import json

@singleton # работает как синглтон
class Settings:
    """Класс обеспечивает чтение, хранение и запись настроек в файл формата JSON"""
    def __init__(self, save_path:Optional[str]):
        self.save_path:Optional[str] = save_path
        self.data:Dict[str,Any] = {}

    def setFilePath(self, path:str):
        self.save_path = path

    def getTitleBarHeight(self):
        style = qApp.style()
        return style.PixelMetric(QStyle.PM_TitleBarHeight)

    def get(self, *keys:str) -> Any:
        """Получение значения настройки по ключам"""
        current_dict: Dict[str,Any] = self.data
        level = 1
        for key in keys:
            if key in current_dict:
                if level < len(keys):
                    if isinstance(current_dict[key], dict):
                        current_dict = current_dict[key]
                        level += 1
                        continue
                    else:
                        return None
                return current_dict[key]
        return None

    def saveTableViewColumnsWidth(self, table_view:QTableView, *keys:str):
        """Сохранение ширины столбцов в QTableView (и его потомках)"""
        if not isinstance(table_view, QTableView):
            return
        rec: Dict[int,int]={}
        for column_index in range(0, table_view.model().columnCount()):
            if not table_view.isColumnHidden(column_index):
                rec[column_index] = table_view.columnWidth(column_index)
        if len(rec) > 0:
            self.set(rec, *keys + ('Columns width',))

    def restoreTableViewColumnsWidth(self, table_view:QTableView, *keys:str):
        """Восстановление ширины столбцов в QTableView (и его потомках)"""
        if not isinstance(table_view, QTableView):
            return
        rec = self.get(*keys + ('Columns width',))
        if rec is None:
            return
        for column_index in rec:
            table_view.setColumnWidth(int(column_index), rec[column_index])

    def saveWidgetGeometry(self, widget:QWidget, *keys:str):
        """Сохранение размера и положения формы"""
        if not isinstance(widget, QWidget):
            return
        edited_keys: List[str] = list(keys) + ['Geometry']
        self.set(widget.x(), *edited_keys+['x'])
        self.set(widget.y(), *edited_keys + ['y'])
        self.set(widget.width(), *edited_keys + ['width'])
        self.set(widget.height(), *edited_keys + ['height'])

    def restoreWidgetGeometry(self, widget:QWidget, *keys:str):
        """Восстановление размера и положения формы"""
        if not isinstance(widget, QWidget):
            return
        edited_keys: List[str] = list(keys) + ['Geometry']
        x:int = self.get(*edited_keys+['x'])
        y:int = self.get(*edited_keys+['y'])
        w:int = self.get(*edited_keys+['width'])
        h:int = self.get(*edited_keys+['height'])
        if x is None or y is None or w is None or h is None:
            return
        widget.setGeometry(x,y + self.getTitleBarHeight(),w,h)

    def set(self, value:Any, *keys:str):
        """Запись значения настройки value по ключам"""
        current_dict: Dict[str, Any] = self.data
        level = 1
        for key in keys:
            if level < len(keys):
                if key not in current_dict:
                    current_dict[key] = {}
                current_dict = current_dict[key]
                level += 1
            else:
                current_dict[key] = value

    def save(self) -> bool:
        """Сохранение файла с настройками"""
        if self.save_path is None:
            print('Путь к файлу для записи не задан.')
            return False
        try:
            with open(self.save_path, 'w') as f:
                json.dump(self.data, f, sort_keys=True, indent=2)
        except OSError as file_error:
            print(f'Ошибка сохранения файла настроек {self.save_path} - {file_error.strerror}')
            return False
        return True

    def load(self) -> bool:
        """Загрузка файла с настройками"""
        if self.save_path is None:
            print('Путь к файлу для чтения не задан.')
            return False
        try:
            with open(self.save_path) as f:
                self.data = json.load(f)
        except OSError as file_error:
            print(f'Ошибка загрузки файла настроек {self.save_path} - {file_error.strerror}')
            return False
        return True