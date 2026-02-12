from PyQt5 import QtWidgets, QtCore, QtGui
import copy
from typing import List, Dict
from BatchedQueryModel import BatchedQueryModel, WhereExpression
import peewee


class FilterDialog(QtWidgets.QDialog):
    """Диалог для управления фильтрами (добавление, изменение, удаление)"""
    _expressions:List[WhereExpression]=None # Список условий фильтра
    _verbose_names:Dict[str,str]=None # Словарь сопоставлений имени полей и их отображаемых имен
    def __init__(self, model_ref:BatchedQueryModel, parent=None):
        super().__init__(parent)
        self._model_ref = model_ref
        # Копируем список условий фильтра
        self._expressions = copy.deepcopy(self._model_ref._where_expressions)
        self._verbose_names = self._verbose_names

        # Инициализация UI
        self.setWindowTitle('Фильтры')
        main_layout = QtWidgets.QVBoxLayout()
        upper_button_layout = QtWidgets.QHBoxLayout()
        self.add_button = QtWidgets.QToolButton()
        self.add_button.setText('➕')
        self.add_button.setToolTip('Добавить')
        upper_button_layout.addWidget(self.add_button)
        upper_button_layout.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        main_layout.addLayout(upper_button_layout,0)
        self.list_view = QtWidgets.QListView()
        main_layout.addWidget(self.list_view,1)
        lower_button_layout = QtWidgets.QHBoxLayout()
        self.ok_button = QtWidgets.QPushButton('ОК')
        self.ok_button.clicked.connect(self.accept)
        lower_button_layout.addWidget(self.ok_button)
        self.cancel_button = QtWidgets.QPushButton('Отмена')
        self.cancel_button.clicked.connect(self.reject)
        lower_button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(lower_button_layout,0)
        self.setLayout(main_layout)

        
