"""
Filter Dialog for document filtering options
"""
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QHBoxLayout, QPushButton, QComboBox, QLineEdit
from PyQt5.QtCore import pyqtSignal
from ..Classes import Document, Branch


class FilterDialog(QDialog):
    """
    Dialog for setting document filters
    """
    filters_applied = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Фильтры документов")
        self.setGeometry(300, 300, 400, 300)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create form for filters
        form_layout = QFormLayout()
        
        # Search term
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по наименованию, ФИО, номеру...")
        form_layout.addRow("Поиск:", self.search_input)
        
        # Document type
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItem("Все типы", "")
        for code, name in Document.DOCUMENT_TYPES:
            self.doc_type_combo.addItem(name, code)
        form_layout.addRow("Тип документа:", self.doc_type_combo)
        
        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItem("Все статусы", "")
        for code, name in Document.STATUSES:
            self.status_combo.addItem(name, code)
        form_layout.addRow("Статус:", self.status_combo)
        
        # Branch
        self.branch_combo = QComboBox()
        self.branch_combo.addItem("Все филиалы", "")
        
        # Load branches
        try:
            for branch in Branch.select():
                self.branch_combo.addItem(branch.name, branch.id)
        except:
            # If database is not initialized yet, skip loading
            pass
        
        form_layout.addRow("Филиал:", self.branch_combo)
        
        # Date range filters
        date_layout = QHBoxLayout()
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setDate(QDate.fromString("2020-01-01", "yyyy-MM-dd"))
        self.start_date_edit.setCalendarPopup(True)
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setCalendarPopup(True)
        date_layout.addWidget(QLabel("С:"))
        date_layout.addWidget(self.start_date_edit)
        date_layout.addWidget(QLabel("По:"))
        date_layout.addWidget(self.end_date_edit)
        form_layout.addRow("Дата отправки:", date_layout)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_btn = QPushButton("Применить")
        self.apply_btn.clicked.connect(self.apply_filters)
        
        self.reset_btn = QPushButton("Сбросить")
        self.reset_btn.clicked.connect(self.reset_filters)
        
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.apply_btn)
        button_layout.addWidget(self.reset_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def apply_filters(self):
        """Apply the selected filters"""
        filters = {}
        
        search_term = self.search_input.text().strip()
        if search_term:
            filters['search_term'] = search_term
            
        doc_type = self.doc_type_combo.currentData()
        if doc_type:
            filters['doc_type'] = doc_type
            
        status = self.status_combo.currentData()
        if status:
            filters['status'] = status
            
        branch_id = self.branch_combo.currentData()
        if branch_id:
            filters['branch_id'] = branch_id
            
        # Add date range filters
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        if start_date != "2020-01-01" or end_date != QDate.currentDate().toString("yyyy-MM-dd"):
            filters['date_from'] = start_date
            filters['date_to'] = end_date
            
        self.filters_applied.emit(filters)
        self.accept()
    
    def reset_filters(self):
        """Reset all filter fields"""
        self.search_input.clear()
        self.doc_type_combo.setCurrentIndex(0)
        self.status_combo.setCurrentIndex(0)
        self.branch_combo.setCurrentIndex(0)