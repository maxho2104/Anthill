from PyQt5 import QtWidgets, QtCore
from typing import Type, Optional
import peewee
from ...common import DBManager, Settings
from ..classes import BaseModel
from ..qt_models import TableModel
from .FilterableTableView import FilterableTableView
from .ItemDialog import ItemDialog



class TableDialog(QtWidgets.QDialog):
    """Диалог для редактирования таблицы"""
    _model:Optional[TableModel] = None
    def __init__(self, peewee_class: Type[BaseModel], parent: QtWidgets.QWidget = None):
        super().__init__(parent)
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self._peewee_class = peewee_class
        self._setting_name = f'{peewee_class.__name__}_dialog'
        self.setWindowTitle(peewee_class.__doc__)
        layout = QtWidgets.QVBoxLayout(self)
        self.table_view = FilterableTableView()
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        layout.addWidget(self.table_view,1)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        self.add_button = QtWidgets.QPushButton('Добавить')
        button_layout.addWidget(self.add_button)
        self.delete_button = QtWidgets.QPushButton('Удалить')
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout,0)

        DBManager().connection_toggled.connect(self.on_database_toggled)
        self.add_button.clicked.connect(self.add_object_by_dialog)
        self.delete_button.clicked.connect(self.delete_selected_rows)

    @QtCore.pyqtSlot()
    def on_database_toggled(self, connected: bool):
        """Действия при изменении состояния базы данных"""
        if connected:
            self._model = TableModel(self._peewee_class)
            self._model.refresh()
        else:
            self._model = None
        self.table_view.setModel(self._model)
        self._model.set_delegates(self.table_view)

    def showEvent(self, event):
        """Действия при открытии окна"""
        Settings().restoreWidgetGeometry(self, 'Forms', self._setting_name)
        if DBManager().connected:
            self.on_database_toggled(True)
            Settings().restoreTableViewColumnsWidth(self.table_view, 'Forms', self._setting_name)
        event.accept()

    def closeEvent(self, event):
        """Действия при закрытии окна"""
        if not self._model is None:
            Settings().saveTableViewColumnsWidth(self.table_view, 'Forms', self._setting_name)
        Settings().saveWidgetGeometry(self, 'Forms', self._setting_name)
        event.accept()

    @QtCore.pyqtSlot()
    def add_object_by_dialog(self):
        """Создание нового объекта (записи БД) через вызов соотв. диалога"""
        # Новый объект получаем вызовом диалога
        new_object = ItemDialog.createObject(self._peewee_class)
        if not new_object is None:
            # Если объект получен (в диалоге нажали "Ок") - записываем в модель
            self._model.append_row(new_object)
            # Покажем пользователю в table_view строку, которую добавили
            row_in_table = self.table_view.row_map_from_source(self._model.rowCount()-1)
            if row_in_table is None:
                return
            self.table_view.scrollTo(self.table_view.proxy_model.index(row_in_table, 0))
            self.table_view.selectRow(row_in_table)
            self.table_view.setFocus()

    @QtCore.pyqtSlot()
    def delete_selected_rows(self):
        """Удаление выделенных строк"""
        # Получим индексы выбранных строк
        rows = self.table_view.get_selected_rows()
        if len(rows) == 0:
            return
        # Удалим их
        for row in sorted(rows, reverse=True):
            self._model.remove_row(row)

