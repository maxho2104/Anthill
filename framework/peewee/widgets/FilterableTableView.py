from PyQt5 import QtWidgets, QtCore
from typing import Optional, List, Dict

class FilterableHeader(QtWidgets.QHeaderView):
    filterChanged = QtCore.pyqtSignal(int, str)
    filterFocused = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget = None):
        super().__init__(QtCore.Qt.Horizontal, parent)
        self._filterWidgets: List[QtWidgets.QLineEdit] = []
        self.setSectionsClickable(True)
        self.setSortIndicatorShown(True)
        self.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        self.setHighlightSections(True)
        self.sectionResized.connect(self.adjustPositions)
        self.sectionClicked.connect(self.adjustPositions)
        parent.horizontalScrollBar().valueChanged.connect(self.adjustPositions)
        parent.verticalScrollBar().valueChanged.connect(self.adjustPositions)

    @QtCore.pyqtSlot(int)
    def generateFilters(self, number:int):
        # Удалить все текущие LineEdit'ы
        for i in range(0,len(self._filterWidgets)):
            self._filterWidgets[i].deleteLater()
        self._filterWidgets.clear()

        # Создать новые LineEdit'ы
        for i in range(0,number):
            lineEdit:QtWidgets.QLineEdit = QtWidgets.QLineEdit(self)
            lineEdit.setPlaceholderText('Фильтр')
            self._filterWidgets.append(lineEdit)
            lineEdit.textChanged.connect(self.inputChanged)
        self.updateGeometries()

    def hasFilters(self)->bool:
        if len(self._filterWidgets) > 0:
            return True
        return False

    @QtCore.pyqtSlot(int,str)
    def setFilter(self, column:int, value:str):
        if column < len(self._filterWidgets):
            self._filterWidgets[column].setText(value)

    def filterValue(self, column:int)->Optional[str]:
        if column < len(self._filterWidgets):
            return self._filterWidgets[column].text()
        return None

    def setFocusColumn(self, column:int)-> None:
        if column < len(self._filterWidgets):
            self._filterWidgets[column].setFocus()

    def sizeHint(self):
        s:QtCore.QSize = super().sizeHint()
        if len(self._filterWidgets) > 0:
            s.setHeight(s.height() + self._filterWidgets[0].sizeHint().height() + 4) #The 4 adds just adds some extra space
        return s

    @QtCore.pyqtSlot()
    def adjustPositions(self):
        #The two adds some extra space between the header label and the input widget
        y:int = super().sizeHint().height() + 2
        for i in range(0, len(self._filterWidgets)):
            line_edit = self._filterWidgets[i]
            if QtWidgets.QApplication.layoutDirection() == QtCore.Qt.RightToLeft:
                line_edit.move(self.width() - (self.sectionPosition(i) + self.sectionSize(i) - self.offset()), y)
            else:
                line_edit.move(self.sectionPosition(i) - self.offset(), y)
            line_edit.resize(self.sectionSize(i), line_edit.sizeHint().height())

    @QtCore.pyqtSlot()
    def clearFilters(self):
        for line_edit in self._filterWidgets:
            line_edit.clear()

    def updateGeometries(self):
        #If there are any input widgets add a viewport margin to the header to generate some empty space for them which is not affected by scrolling
        if len(self._filterWidgets) > 0:
            self.setViewportMargins(0,0,0, self._filterWidgets[0].sizeHint().height())
        else:
            self.setViewportMargins(0,0,0,0)
        super().updateGeometries()
        self.adjustPositions()

    @QtCore.pyqtSlot(str)
    def inputChanged(self, new_value:str):
        self.adjustPositions()
        line_edit:QtWidgets.QLineEdit = self.sender()
        self.filterChanged.emit(self._filterWidgets.index(line_edit), new_value)

class MySortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent:QtCore.QObject=None):
        super().__init__(parent)
        self.filters: Dict[int, str] = {}

    def updateFilter(self, column:int, filter_str:str):
        self.beginResetModel()
        if len(filter_str) == 0:
            if column in self.filters.keys():
                del self.filters[column]
        else:
            self.filters[column] = filter_str
        self.endResetModel()

    def filterAcceptsRow(self, source_row, source_parent):
        for column in range(0,self.sourceModel().columnCount()):
            if column in self.filters.keys():
                #Пока фильтруем лишь строки
                column_value = self.sourceModel().data(self.sourceModel().index(source_row, column, source_parent), QtCore.Qt.DisplayRole)
                if isinstance(column_value, str):
                    column_str = column_value
                elif isinstance(column_value, (int, float)):
                    column_str = str(column_value)
                elif isinstance(column_value, QtCore.QDateTime):
                    column_str = column_value.toString('dd.MM.yyyy hh:mm')
                elif isinstance(column_value, QtCore.QDate):
                    column_str = column_str = column_value.toString('dd.MM.yyyy')
                if QtCore.QRegExp(self.filters[column], QtCore.Qt.CaseInsensitive).indexIn(column_str) == -1:
                    return False
        return True

class FilterableTableView(QtWidgets.QTableView):
    """QTableView с поддержкой сортировки и фильтрации по каждому столбцу"""

    rowCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        # Исходная модель
        self.source_model:QtCore.QAbstractItemModel = None
        # Прокси-модель для сортировки и фильтрации
        self.proxy_model = MySortFilterProxyModel(self)
        self.proxy_model.setFilterKeyColumn(-1)  # по умолчанию все колонки
        self.proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        # включаем сортировку
        self.setSortingEnabled(True)
        # Виджет для фильтров
        self._filter_widget = None

    def setModel(self, model):
        if model is None:
            self.source_model = None
            return
        self.source_model = model
        # оборачиваем модель в прокси
        self.proxy_model.setSourceModel(model)
        super().setModel(self.proxy_model)
        # Проверяем, заголовок нужного формата, если нет - создаем заголовок с фильтрами
        existing_header = self.horizontalHeader()
        if not isinstance(existing_header, FilterableHeader):
            horizontalHeader = FilterableHeader(self)
            horizontalHeader.generateFilters(model.columnCount())
            self.setHorizontalHeader(horizontalHeader)
            horizontalHeader.filterChanged.connect(self.updateFilter)

    def model(self):
        return self.proxy_model.sourceModel()

    def selectedIndexes(self):
        return [self.proxy_model.mapToSource(index) for index in super().selectedIndexes()]

    @QtCore.pyqtSlot(int, str)
    def updateFilter(self, column:int, filter_str:str):
        self.verticalHeader().setMinimumWidth(self.verticalHeader().width())
        if isinstance(self.proxy_model, MySortFilterProxyModel):
            oldRowCount = self.proxy_model.rowCount()
            self.proxy_model.updateFilter(column, filter_str)
            newRowCount = self.proxy_model.rowCount()
            if oldRowCount != newRowCount: self.rowCountChanged.emit(newRowCount)
        horizontalHeader = self.horizontalHeader()
        if isinstance(horizontalHeader, FilterableHeader):
            horizontalHeader.adjustPositions()