from PyQt5 import QtWidgets, QtCore
import peewee
from typing import Callable,List, Dict, Any
from BatchedQueryModel import BatchedQueryModel, WhereExpression
from FilterDialog import FilterDialog
from framework import Settings

class QueryWidget(QtWidgets.QWidget):
    """Виджет для отображения данных из базы по запросу"""
    def __init__(self, query:peewee.ModelSelect=None, header_names:List[str]=None,
                 user_data_func:Callable[[List[Dict[str,Any]],QtCore.QModelIndex, int], Any]=None,
                 where_expressions:List[WhereExpression]=None, verbose_names:Dict[str, str]=None, parent=None):
        super().__init__(parent)
        # Создание UI
        layout = QtWidgets.QVBoxLayout()
        button_layout = QtWidgets.QHBoxLayout()
        self.filter_button = QtWidgets.QPushButton('Фильтр')
        button_layout.addWidget(self.filter_button)
        self.order_button = QtWidgets.QPushButton('Сортировка')
        button_layout.addWidget(self.order_button)
        self.update_button = QtWidgets.QPushButton('Обновить')
        button_layout.addWidget(self.update_button)
        button_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        layout.addLayout(button_layout,0)
        self.table_view = QtWidgets.QTableView()
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.table_view,1)
        self.setLayout(layout)
        # Инициализация модели
        self.model = BatchedQueryModel(query, header_names, user_data_func, where_expressions, verbose_names, self)
        self.table_view.setModel(self.model)

        self.update_button.clicked.connect(self.model.refresh)
        self.filter_button.clicked.connect(self.show_filter_dialog)

    def showEvent(self, event):
        """Действия при открытии окна"""
        Settings().restoreWidgetGeometry(self, 'Forms', f'{self.model.base_peewee_model().__name__}_widget')
        Settings().restoreTableViewColumnsWidth(self.table_view, 'Forms', f'{self.model.base_peewee_model().__name__}_widget')
        event.accept()

    def closeEvent(self, event):
        """Действия при закрытии окна"""
        Settings().saveTableViewColumnsWidth(self.table_view, 'Forms', f'{self.model.base_peewee_model().__name__}_widget')
        Settings().saveWidgetGeometry(self, 'Forms', f'{self.model.base_peewee_model().__name__}_widget')
        Settings().save()
        event.accept()

    def show_filter_dialog(self):
        """Показывает диалог фильтров"""
        dialog = FilterDialog(self.model, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            # Обновить модель после применения фильтров
            self.model.refresh()


