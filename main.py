#!/usr/bin/env python3
"""
Main application for document workflow management system
This application automates the activities of enterprise documentation staff 
for accounting of internal correspondence between headquarters and branches.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QListWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QTextEdit, QFormLayout, QDialog, QComboBox, QDateEdit, QMenu, QAction, QTableView
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import json
from datetime import datetime
import zipfile
import shutil
from pathlib import Path

from Peewee.Classes import initialize_db


class DocumentWorkflowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета внутренней корреспонденции")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize database
        self.db_path = "documents.db"
        self.storage_path = "document_storage"
        self.db = initialize_db()
        self.create_storage_directory()
        
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create tab widget for different functions
        self.tabs = QTabWidget()
        self.setup_tabs()
        main_layout.addWidget(self.tabs)
        
        # Status bar
        self.statusBar().showMessage('Готов')
    
    def setup_tabs(self):
        """Setup application tabs"""
        # Documents tab
        self.documents_tab = DocumentsTab(self)
        self.tabs.addTab(self.documents_tab, "Документы")
        
        # Statistics tab
        self.statistics_tab = StatisticsTab(self)
        self.tabs.addTab(self.statistics_tab, "Статистика")
        
        # Export/Import tab
        self.export_import_tab = ExportImportTab(self)
        self.tabs.addTab(self.export_import_tab, "Экспорт/Импорт")
    
    def create_storage_directory(self):
        """Create document storage directory if it doesn't exist"""
        if not os.path.exists(self.storage_path):
            os.makedirs(self.storage_path)


class DocumentsTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.init_ui()
    
    def init_ui(self):
        """Initialize the documents tab UI"""
        layout = QVBoxLayout()
        
        # Button for filters
        self.filters_button = QPushButton("Фильтры")
        self.filters_button.clicked.connect(self.open_filters)
        layout.addWidget(self.filters_button)
        
        # Documents table view using QTableView
        self.documents_table = QTableView()
        self.documents_table.setSelectionBehavior(QTableView.SelectRows)  # Select entire rows
        self.documents_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.documents_table.customContextMenuRequested.connect(self.context_menu)
        self.documents_table.doubleClicked.connect(self.edit_document)  # Double click to edit
        
        layout.addWidget(self.documents_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_document_btn = QPushButton("Добавить документ")
        self.add_document_btn.clicked.connect(self.add_document)
        
        self.edit_selected_btn = QPushButton("Редактировать")
        self.edit_selected_btn.clicked.connect(self.edit_document)
        
        self.delete_document_btn = QPushButton("Удалить документ")
        self.delete_document_btn.clicked.connect(self.delete_document)
        
        button_layout.addWidget(self.add_document_btn)
        button_layout.addWidget(self.edit_selected_btn)
        button_layout.addWidget(self.delete_document_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Initialize the table model
        from Peewee.Classes.table_model import DocumentTableModel
        self.model = DocumentTableModel(batch_size=100)
        self.documents_table.setModel(self.model)
        self.model.load_data()  # Load initial data
    
    def open_filters(self):
        """Open filter dialog"""
        from Peewee.Classes.filter_dialog import FilterDialog
        dialog = FilterDialog(self)
        dialog.filters_applied.connect(self.apply_filters)
        dialog.exec_()
    
    def apply_filters(self, filters):
        """Apply filters to the model"""
        self.model.clear_data()
        self.model.load_data(filters=filters)
    
    def context_menu(self, position):
        """Show context menu on right-click"""
        menu = QMenu()
        edit_action = menu.addAction("Изменить")
        delete_action = menu.addAction("Удалить")
        
        action = menu.exec_(self.documents_table.mapToGlobal(position))
        
        if action == edit_action:
            self.edit_document()
        elif action == delete_action:
            self.delete_document()
    
    def add_document(self):
        """Add new document"""
        dialog = DocumentDialog(self.main_app)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()
    
    def edit_document(self):
        """Edit selected document"""
        selected_indexes = self.documents_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите документ для редактирования")
            return
        
        # Get the document from the model
        row = selected_indexes[0].row()
        document = self.model.data_list[row]
        
        dialog = DocumentDialog(self.main_app, document.id)
        if dialog.exec_() == QDialog.Accepted:
            self.refresh_data()
    
    def delete_document(self):
        """Delete selected document"""
        selected_indexes = self.documents_table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Ошибка", "Выберите документ для удаления")
            return
        
        # Get the document from the model
        row = selected_indexes[0].row()
        document = self.model.data_list[row]
        
        reply = QMessageBox.question(
            self, 
            "Подтверждение", 
            "Вы уверены, что хотите удалить выбранный документ?",
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Remove associated file if it exists
                if document.file_path and os.path.exists(document.file_path):
                    os.remove(document.file_path)
                
                # Delete from database
                document.delete_instance()
                
                # Refresh the table
                self.refresh_data()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка при удалении документа: {str(e)}")
    
    def refresh_data(self):
        """Refresh the displayed data"""
        # Get current filters
        filters = self.model.filters
        self.model.clear_data()
        self.model.load_data(filters=filters)


class DocumentDialog(QDialog):
    def __init__(self, main_app, doc_id=None):
        super().__init__()
        self.main_app = main_app
        self.doc_id = doc_id
        self.setWindowTitle("Документ" if doc_id else "Новый документ")
        self.setGeometry(200, 200, 600, 700)
        
        # Load document object if editing
        self.document = None
        if doc_id:
            from Peewee.Classes import Document
            try:
                self.document = Document.get_by_id(doc_id)
            except:
                QMessageBox.critical(self, "Ошибка", "Документ не найден")
                self.reject()
        
        self.init_ui()
        if self.document:
            self.load_document_data()
    
    def init_ui(self):
        """Initialize document dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout for document properties
        form_layout = QFormLayout()
        
        # Document type
        self.doc_type_combo = QComboBox()
        for code, name in [('main', 'Основной'), ('additional', 'Дополнительный'), ('report', 'Отчетный'), ('other', 'Прочий')]:
            self.doc_type_combo.addItem(name, code)
        form_layout.addRow("Тип документа:", self.doc_type_combo)
        
        # Title
        self.title_edit = QLineEdit()
        form_layout.addRow("Наименование:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_edit)
        
        # Sender branch
        self.sender_branch_combo = QComboBox()
        from Peewee.Classes import Branch
        for branch in Branch.select():
            self.sender_branch_combo.addItem(branch.name, branch.id)
        form_layout.addRow("Филиал отправителя:", self.sender_branch_combo)
        
        # Sender department
        self.sender_dept_combo = QComboBox()
        from Peewee.Classes import Department
        for dept in Department.select():
            self.sender_dept_combo.addItem(dept.name, dept.id)
        form_layout.addRow("Отдел отправителя:", self.sender_dept_combo)
        
        # Sender position
        self.sender_pos_edit = QLineEdit()
        form_layout.addRow("Должность отправителя:", self.sender_pos_edit)
        
        # Sender FIO
        self.sender_fio_edit = QLineEdit()
        form_layout.addRow("ФИО отправителя:", self.sender_fio_edit)
        
        # Outgoing number and date
        outgoing_layout = QHBoxLayout()
        self.outgoing_number_edit = QLineEdit()
        self.outgoing_date_edit = QDateEdit()
        self.outgoing_date_edit.setDate(QDate.currentDate())
        self.outgoing_date_edit.setCalendarPopup(True)
        outgoing_layout.addWidget(self.outgoing_number_edit)
        outgoing_layout.addWidget(self.outgoing_date_edit)
        form_layout.addRow("Исх. № и дата:", outgoing_layout)
        
        # Incoming number and date
        incoming_layout = QHBoxLayout()
        self.incoming_number_edit = QLineEdit()
        self.incoming_date_edit = QDateEdit()
        self.incoming_date_edit.setDate(QDate.currentDate())
        self.incoming_date_edit.setCalendarPopup(True)
        incoming_layout.addWidget(self.incoming_number_edit)
        incoming_layout.addWidget(self.incoming_date_edit)
        form_layout.addRow("Вх. № и дата:", incoming_layout)
        
        # Evaluator
        self.evaluator_edit = QLineEdit()
        form_layout.addRow("Оценивающий:", self.evaluator_edit)
        
        # Evaluation
        self.evaluation_combo = QComboBox()
        self.evaluation_combo.addItem("", "")  # Empty option
        for code, name in [('excellent', 'Отлично'), ('good', 'Хорошо'), ('satisfactory', 'Удовлетворительно'), ('unsatisfactory', 'Неудовлетворительно')]:
            self.evaluation_combo.addItem(name, code)
        form_layout.addRow("Оценка:", self.evaluation_combo)
        
        # Evaluation date
        self.evaluation_date_edit = QDateEdit()
        self.evaluation_date_edit.setDate(QDate.currentDate())
        self.evaluation_date_edit.setCalendarPopup(True)
        form_layout.addRow("Дата оценки:", self.evaluation_date_edit)
        
        # File selection
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setReadOnly(True)
        self.select_file_btn = QPushButton("Выбрать файл")
        self.select_file_btn.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.select_file_btn)
        form_layout.addRow("Файл документа:", file_layout)
        
        # Status
        self.status_combo = QComboBox()
        for code, name in [('sent', 'Отправлен'), ('received', 'Получен'), ('evaluating', 'На оценке'), ('evaluated', 'Оценен'), ('archived', 'Архив')]:
            self.status_combo.addItem(name, code)
        form_layout.addRow("Статус:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_document)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def select_file(self):
        """Select document file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл документа", 
            "", 
            "Документы (*.doc *.docx *.rtf *.pdf *.xls *.xlsx *.txt *.json)"
        )
        if file_path:
            # Copy file to storage directory
            filename = os.path.basename(file_path)
            target_path = os.path.join(self.main_app.storage_path, filename)
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(target_path)
            while os.path.exists(target_path):
                target_path = f"{base_name}_{counter}{ext}"
                counter += 1
            
            shutil.copy2(file_path, target_path)
            self.file_path_edit.setText(target_path)
    
    def save_document(self):
        """Save document to database using Peewee"""
        # Validate required fields
        if not self.title_edit.text():
            QMessageBox.warning(self, "Ошибка", "Введите наименование документа")
            return
        
        if self.sender_branch_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите филиал отправителя")
            return
        
        from Peewee.Classes import Document, Branch, Department
        
        try:
            # Get selected branch and department
            branch_id = self.sender_branch_combo.currentData()
            dept_id = self.sender_dept_combo.currentData()
            
            # Get branch and department objects
            branch = Branch.get_by_id(branch_id)
            department = Department.get_by_id(dept_id) if dept_id else None
            
            # Prepare data
            doc_data = {
                'doc_type': self.doc_type_combo.currentData(),
                'title': self.title_edit.text(),
                'description': self.description_edit.toPlainText() or None,
                'sender_branch': branch,
                'sender_department': department,
                'sender_position': self.sender_pos_edit.text() or None,
                'sender_fio': self.sender_fio_edit.text(),
                'outgoing_number': self.outgoing_number_edit.text() or None,
                'outgoing_date': self.outgoing_date_edit.date().toPyDate() if self.outgoing_date_edit.date().isValid() else None,
                'incoming_number': self.incoming_number_edit.text() or None,
                'incoming_date': self.incoming_date_edit.date().toPyDate() if self.incoming_date_edit.date().isValid() else None,
                'evaluator': self.evaluator_edit.text() or None,
                'evaluation': self.evaluation_combo.currentData() or None,
                'evaluation_date': self.evaluation_date_edit.date().toPyDate() if self.evaluation_date_edit.date().isValid() else None,
                'file_path': self.file_path_edit.text() or None,
                'status': self.status_combo.currentData()
            }
            
            if self.document:
                # Update existing document
                for attr, value in doc_data.items():
                    setattr(self.document, attr, value)
                self.document.save()
            else:
                # Create new document
                Document.create(**doc_data)
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при сохранении документа: {str(e)}")
    
    def load_document_data(self):
        """Load existing document data for editing"""
        if self.document:
            # Map document type to combo box
            doc_type_map = dict([('main', 'Основной'), ('additional', 'Дополнительный'), ('report', 'Отчетный'), ('other', 'Прочий')])
            idx = self.doc_type_combo.findData(self.document.doc_type)
            if idx >= 0:
                self.doc_type_combo.setCurrentIndex(idx)
            
            self.title_edit.setText(self.document.title)
            self.description_edit.setPlainText(self.document.description or "")
            
            # Set branch
            branch_idx = self.sender_branch_combo.findData(self.document.sender_branch.id)
            if branch_idx >= 0:
                self.sender_branch_combo.setCurrentIndex(branch_idx)
            
            # Set department
            if self.document.sender_department:
                dept_idx = self.sender_dept_combo.findData(self.document.sender_department.id)
                if dept_idx >= 0:
                    self.sender_dept_combo.setCurrentIndex(dept_idx)
            
            self.sender_pos_edit.setText(self.document.sender_position or "")
            self.sender_fio_edit.setText(self.document.sender_fio)
            self.outgoing_number_edit.setText(self.document.outgoing_number or "")
            
            if self.document.outgoing_date:
                self.outgoing_date_edit.setDate(self.document.outgoing_date)
            
            self.incoming_number_edit.setText(self.document.incoming_number or "")
            if self.document.incoming_date:
                self.incoming_date_edit.setDate(self.document.incoming_date)
            
            self.evaluator_edit.setText(self.document.evaluator or "")
            
            # Set evaluation
            eval_idx = self.evaluation_combo.findData(self.document.evaluation)
            if eval_idx >= 0:
                self.evaluation_combo.setCurrentIndex(eval_idx)
            
            if self.document.evaluation_date:
                self.evaluation_date_edit.setDate(self.document.evaluation_date)
            
            self.file_path_edit.setText(self.document.file_path or "")
            
            # Set status
            status_idx = self.status_combo.findData(self.document.status)
            if status_idx >= 0:
                self.status_combo.setCurrentIndex(status_idx)


class StatisticsTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.init_ui()
    
    def init_ui(self):
        """Initialize statistics tab UI"""
        layout = QVBoxLayout()
        
        # Controls for generating statistics
        controls_layout = QHBoxLayout()
        
        self.branch_filter = QComboBox()
        self.branch_filter.addItem("Все филиалы", None)
        # Load branches from database
        self.load_branches()
        
        self.period_combo = QComboBox()
        self.period_combo.addItems(["Месяц", "Квартал", "Год", "Произвольный период"])
        
        self.generate_btn = QPushButton("Сформировать статистику")
        self.generate_btn.clicked.connect(self.generate_statistics)
        
        controls_layout.addWidget(QLabel("Филиал:"))
        controls_layout.addWidget(self.branch_filter)
        controls_layout.addWidget(QLabel("Период:"))
        controls_layout.addWidget(self.period_combo)
        controls_layout.addWidget(self.generate_btn)
        
        layout.addLayout(controls_layout)
        
        # Statistics display
        self.stats_display = QTextEdit()
        self.stats_display.setReadOnly(True)
        layout.addWidget(self.stats_display)
        
        self.setLayout(layout)
    
    def load_branches(self):
        """Load branches from database"""
        from Peewee.Classes import Branch
        
        try:
            for branch in Branch.select():
                self.branch_filter.addItem(branch.name, branch.id)
        except:
            pass  # Database might not be initialized yet
    
    def generate_statistics(self):
        """Generate statistics based on filters"""
        from Peewee.Classes import Document, Branch
        
        selected_branch_id = self.branch_filter.currentData()
        period = self.period_combo.currentText()
        
        # Build query
        query = Document.select()
        
        if selected_branch_id is not None:
            query = query.where(Document.sender_branch == selected_branch_id)
        
        # For now, don't filter by period, but we could add date filtering here
        
        records = list(query)
        
        # Calculate statistics
        total_docs = len(records)
        
        # Count by evaluation
        eval_counts = {"Отлично": 0, "Хорошо": 0, "Удовлетворительно": 0, "Неудовлетворительно": 0, "Без оценки": 0}
        eval_map = dict(Document.EVALUATIONS)
        rev_eval_map = {v: k for k, v in eval_map.items()}  # Reverse mapping
        
        for record in records:
            evaluation = record.evaluation
            if evaluation:
                display_eval = eval_map.get(evaluation, evaluation)
                if display_eval in eval_counts:
                    eval_counts[display_eval] += 1
                else:
                    eval_counts["Без оценки"] += 1
            else:
                eval_counts["Без оценки"] += 1
        
        # Count by status
        status_counts = {}
        status_map = dict(Document.STATUSES)
        for record in records:
            status = record.status
            if status:
                display_status = status_map.get(status, status)
                status_counts[display_status] = status_counts.get(display_status, 0) + 1
            else:
                status_counts["Без статуса"] = status_counts.get("Без статуса", 0) + 1
        
        # Count by department
        dept_counts = {}
        for record in records:
            dept = record.sender_department
            if dept:
                dept_counts[dept.name] = dept_counts.get(dept.name, 0) + 1
            else:
                dept_counts["Без отдела"] = dept_counts.get("Без отдела", 0) + 1
        
        # Format statistics
        branch_name = "Все филиалы"
        if selected_branch_id is not None:
            try:
                branch = Branch.get_by_id(selected_branch_id)
                branch_name = branch.name
            except:
                branch_name = "Филиал не найден"
        
        stats_text = f"""Статистика по документам
Фильтр: {branch_name}, Период: {period}

Общее количество документов: {total_docs}

Распределение по оценкам:
"""
        for eval_val, count in eval_counts.items():
            stats_text += f"  {eval_val}: {count}\n"
        
        stats_text += "\nРаспределение по статусам:\n"
        for status, count in status_counts.items():
            stats_text += f"  {status}: {count}\n"
        
        stats_text += "\nРаспределение по отделам:\n"
        for dept, count in dept_counts.items():
            stats_text += f"  {dept}: {count}\n"
        
        self.stats_display.setPlainText(stats_text)


class ExportImportTab(QWidget):
    def __init__(self, main_app):
        super().__init__()
        self.main_app = main_app
        self.init_ui()
    
    def init_ui(self):
        """Initialize export/import tab UI"""
        layout = QVBoxLayout()
        
        # Export section
        export_group = QWidget()
        export_layout = QVBoxLayout(export_group)
        
        export_title = QLabel("Экспорт документов")
        export_title.setStyleSheet("font-weight: bold;")
        export_layout.addWidget(export_title)
        
        self.export_branch = QComboBox()
        self.load_branches()
        
        export_controls = QHBoxLayout()
        export_controls.addWidget(QLabel("Филиал:"))
        export_controls.addWidget(self.export_branch)
        
        self.export_btn = QPushButton("Сформировать экспортный файл")
        self.export_btn.clicked.connect(self.export_documents)
        export_controls.addWidget(self.export_btn)
        
        export_layout.addLayout(export_controls)
        
        layout.addWidget(export_group)
        
        # Import section
        import_group = QWidget()
        import_layout = QVBoxLayout(import_group)
        
        import_title = QLabel("Импорт документов")
        import_title.setStyleSheet("font-weight: bold;")
        import_layout.addWidget(import_title)
        
        import_controls = QHBoxLayout()
        self.import_file_path = QLineEdit()
        self.import_file_path.setReadOnly(True)
        self.select_import_btn = QPushButton("Выбрать файл импорта")
        self.select_import_btn.clicked.connect(self.select_import_file)
        self.import_btn = QPushButton("Импортировать")
        self.import_btn.clicked.connect(self.import_documents)
        
        import_controls.addWidget(self.import_file_path)
        import_controls.addWidget(self.select_import_btn)
        import_layout.addLayout(import_controls)
        import_layout.addWidget(self.import_btn)
        
        layout.addWidget(import_group)
        
        # Evaluation import section
        eval_group = QWidget()
        eval_layout = QVBoxLayout(eval_group)
        
        eval_title = QLabel("Импорт оценок")
        eval_title.setStyleSheet("font-weight: bold;")
        eval_layout.addWidget(eval_title)
        
        eval_controls = QHBoxLayout()
        self.eval_file_path = QLineEdit()
        self.eval_file_path.setReadOnly(True)
        self.select_eval_btn = QPushButton("Выбрать файл оценок")
        self.select_eval_btn.clicked.connect(self.select_eval_file)
        self.import_eval_btn = QPushButton("Импортировать оценки")
        self.import_eval_btn.clicked.connect(self.import_evaluations)
        
        eval_controls.addWidget(self.eval_file_path)
        eval_controls.addWidget(self.select_eval_btn)
        eval_layout.addLayout(eval_controls)
        eval_layout.addWidget(self.import_eval_btn)
        
        layout.addWidget(eval_group)
        
        self.setLayout(layout)
    
    def load_branches(self):
        """Load branches for export filter"""
        from Peewee.Classes import Branch
        
        self.export_branch.addItem("Все филиалы", None)
        
        try:
            for branch in Branch.select():
                self.export_branch.addItem(branch.name, branch.id)
        except:
            pass  # Database might not be initialized yet
    
    def export_documents(self):
        """Export documents to ZIP archive"""
        from Peewee.Classes import Document, Branch
        
        selected_branch_id = self.export_branch.currentData()
        
        # Build query
        query = Document.select().order_by(Document.created_at.desc())
        
        if selected_branch_id is not None:
            query = query.where(Document.sender_branch == selected_branch_id)
        
        records = list(query)
        
        # Create export data
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source_branch": self.export_branch.currentText(),
            "documents": []
        }
        
        for record in records:
            doc_dict = {
                "id": record.id,
                "doc_type": record.doc_type,
                "title": record.title,
                "description": record.description,
                "sender_branch": record.sender_branch.name,
                "sender_department": record.sender_department.name if record.sender_department else None,
                "sender_position": record.sender_position,
                "sender_fio": record.sender_fio,
                "outgoing_number": record.outgoing_number,
                "outgoing_date": str(record.outgoing_date) if record.outgoing_date else None,
                "incoming_number": record.incoming_number,
                "incoming_date": str(record.incoming_date) if record.incoming_date else None,
                "evaluator": record.evaluator,
                "evaluation": record.evaluation,
                "evaluation_date": str(record.evaluation_date) if record.evaluation_date else None,
                "file_path": record.file_path,
                "status": record.status,
                "created_at": str(record.created_at)
            }
            export_data["documents"].append(doc_dict)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        branch_name = self.export_branch.currentText().replace(' ', '_') if selected_branch_id is not None else "all"
        filename = f"export_{branch_name}_{timestamp}.zip"
        
        # Create ZIP file with JSON metadata and document files
        with zipfile.ZipFile(filename, 'w') as zipf:
            # Add metadata JSON
            zipf.writestr('metadata.json', json.dumps(export_data, ensure_ascii=False, indent=2))
            
            # Add document files
            for doc in export_data["documents"]:
                file_path = doc.get("file_path")
                if file_path and os.path.exists(file_path):
                    # Store just the filename in the archive
                    arcname = f"documents/{os.path.basename(file_path)}"
                    zipf.write(file_path, arcname)
        
        QMessageBox.information(self, "Экспорт завершен", f"Файл экспорта создан: {filename}")
    
    def select_import_file(self):
        """Select import file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл импорта", 
            "", 
            "ZIP Files (*.zip)"
        )
        if file_path:
            self.import_file_path.setText(file_path)
    
    def select_eval_file(self):
        """Select evaluation file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Выберите файл оценок", 
            "", 
            "JSON Files (*.json);;ZIP Files (*.zip)"
        )
        if file_path:
            self.eval_file_path.setText(file_path)
    
    def import_documents(self):
        """Import documents from ZIP archive"""
        file_path = self.import_file_path.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Выберите файл импорта")
            return
        
        try:
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # Extract metadata
                metadata_content = zipf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_content)
                
                # Extract and save documents
                conn = sqlite3.connect(self.main_app.db_path)
                cursor = conn.cursor()
                
                imported_count = 0
                for doc_data in metadata.get("documents", []):
                    # Check if document already exists (by ID or other unique key)
                    cursor.execute(
                        "SELECT id FROM documents WHERE outgoing_number=? AND outgoing_date=?",
                        (doc_data.get("outgoing_number"), doc_data.get("outgoing_date"))
                    )
                    
                    if not cursor.fetchone():
                        # Save document file if present in archive
                        doc_filename = None
                        if doc_data.get("file_path"):
                            original_filename = os.path.basename(doc_data["file_path"])
                            doc_arcname = f"documents/{original_filename}"
                            
                            # Extract file to storage
                            for zip_info in zipf.filelist:
                                if zip_info.filename.startswith(f"documents/{original_filename}"):
                                    extracted_path = zipf.extract(zip_info, self.main_app.storage_path)
                                    doc_filename = extracted_path
                                    break
                        
                        # Insert document into database
                        cursor.execute('''
                            INSERT INTO documents (
                                doc_type, title, description, sender_branch,
                                sender_department, sender_position, sender_fio,
                                outgoing_number, outgoing_date, incoming_number,
                                incoming_date, evaluator, evaluation,
                                evaluation_date, file_path, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            doc_data.get("doc_type", ""),
                            doc_data.get("title", ""),
                            doc_data.get("description", ""),
                            doc_data.get("sender_branch", ""),
                            doc_data.get("sender_department", ""),
                            doc_data.get("sender_position", ""),
                            doc_data.get("sender_fio", ""),
                            doc_data.get("outgoing_number", ""),
                            doc_data.get("outgoing_date", ""),
                            doc_data.get("incoming_number", ""),
                            doc_data.get("incoming_date", ""),
                            doc_data.get("evaluator", ""),
                            doc_data.get("evaluation", ""),
                            doc_data.get("evaluation_date", ""),
                            doc_filename,
                            doc_data.get("status", "Получен")
                        ))
                        
                        imported_count += 1
                
                conn.commit()
                conn.close()
                
                QMessageBox.information(
                    self, 
                    "Импорт завершен", 
                    f"Импортировано документов: {imported_count}"
                )
                
                # Refresh documents list
                parent_tab = self.parent().parent()  # Navigate to DocumentsTab
                if hasattr(parent_tab, 'documents_tab'):
                    parent_tab.documents_tab.load_documents()
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", f"Ошибка при импорте: {str(e)}")
    
    def import_evaluations(self):
        """Import evaluations from JSON file"""
        file_path = self.eval_file_path.text()
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Ошибка", "Выберите файл оценок")
            return
        
        try:
            # Determine if it's a ZIP file or JSON file
            if file_path.lower().endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zipf:
                    # Look for JSON files in the archive
                    json_files = [f for f in zipf.namelist() if f.endswith('.json')]
                    if not json_files:
                        raise Exception("No JSON files found in archive")
                    
                    # Read the first JSON file
                    content = zipf.read(json_files[0]).decode('utf-8')
                    evaluations = json.loads(content)
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    evaluations = json.load(f)
            
            # Update document evaluations in database
            conn = sqlite3.connect(self.main_app.db_path)
            cursor = conn.cursor()
            
            updated_count = 0
            for eval_data in evaluations.get("evaluations", []):
                outgoing_num = eval_data.get("outgoing_number")
                outgoing_date = eval_data.get("outgoing_date")
                evaluation = eval_data.get("evaluation")
                
                if outgoing_num and evaluation:
                    cursor.execute('''
                        UPDATE documents 
                        SET evaluation=?, evaluation_date=?
                        WHERE outgoing_number=? AND outgoing_date=?
                    ''', (evaluation, datetime.now().date().isoformat(), outgoing_num, outgoing_date))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
            
            conn.commit()
            conn.close()
            
            QMessageBox.information(
                self, 
                "Импорт оценок завершен", 
                f"Обновлено оценок: {updated_count}"
            )
            
            # Refresh documents list
            parent_tab = self.parent().parent()  # Navigate to DocumentsTab
            if hasattr(parent_tab, 'documents_tab'):
                parent_tab.documents_tab.load_documents()
        
        except Exception as e:
            QMessageBox.critical(self, "Ошибка импорта", f"Ошибка при импорте оценок: {str(e)}")


def main():
    app = QApplication(sys.argv)
    window = DocumentWorkflowApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()