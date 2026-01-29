#!/usr/bin/env python3
"""
Main application for document workflow management system
This application automates the activities of enterprise documentation staff 
for accounting of internal correspondence between headquarters and branches.
"""

import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, QPushButton, QFileDialog, QMessageBox, QListWidget, QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QTextEdit, QFormLayout, QDialog, QComboBox, QDateEdit, QMenu, QAction
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QIcon
import json
import sqlite3
from datetime import datetime
import zipfile
import shutil
from pathlib import Path


class DocumentWorkflowApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Система учета внутренней корреспонденции")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize database
        self.db_path = "documents.db"
        self.storage_path = "document_storage"
        self.init_database()
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
    
    def init_database(self):
        """Initialize SQLite database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create documents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                sender_branch TEXT NOT NULL,
                sender_department TEXT,
                sender_position TEXT,
                sender_fio TEXT,
                outgoing_number TEXT,
                outgoing_date DATE,
                incoming_number TEXT,
                incoming_date DATE,
                evaluator TEXT,
                evaluation TEXT,
                evaluation_date DATE,
                file_path TEXT,
                status TEXT DEFAULT 'sent',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create branches table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS branches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                address TEXT,
                contact_person TEXT
            )
        ''')
        
        # Create departments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                branch_id INTEGER,
                FOREIGN KEY (branch_id) REFERENCES branches (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
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
        
        # Search form
        search_group = QWidget()
        search_layout = QHBoxLayout(search_group)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Поиск по реквизитам документа...")
        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.search_documents)
        
        search_layout.addWidget(QLabel("Поиск:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        
        layout.addWidget(search_group)
        
        # Documents table
        self.documents_table = QTableWidget()
        self.documents_table.setColumnCount(12)
        self.documents_table.setHorizontalHeaderLabels([
            "ID", "Тип", "Наименование", "Филиал", "Отдел", "Отправитель", 
            "Исх. №", "Исх. дата", "Вх. №", "Вх. дата", "Оценка", "Статус"
        ])
        
        # Set header stretch
        header = self.documents_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        layout.addWidget(self.documents_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.add_document_btn = QPushButton("Добавить документ")
        self.add_document_btn.clicked.connect(self.add_document)
        
        self.edit_document_btn = QPushButton("Редактировать документ")
        self.edit_document_btn.clicked.connect(self.edit_document)
        
        self.delete_document_btn = QPushButton("Удалить документ")
        self.delete_document_btn.clicked.connect(self.delete_document)
        
        button_layout.addWidget(self.add_document_btn)
        button_layout.addWidget(self.edit_document_btn)
        button_layout.addWidget(self.delete_document_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.load_documents()
    
    def load_documents(self):
        """Load documents from database to table"""
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM documents ORDER BY created_at DESC')
        records = cursor.fetchall()
        
        self.documents_table.setRowCount(len(records))
        
        for row_idx, record in enumerate(records):
            for col_idx, value in enumerate(record):
                item = QTableWidgetItem(str(value) if value else "")
                self.documents_table.setItem(row_idx, col_idx, item)
        
        conn.close()
    
    def search_documents(self):
        """Search documents by criteria"""
        search_term = self.search_input.text().strip().lower()
        if not search_term:
            self.load_documents()
            return
        
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        # Get all documents first (we'll filter in Python to handle Cyrillic properly)
        cursor.execute('SELECT * FROM documents ORDER BY created_at DESC')
        all_records = cursor.fetchall()
        
        # Filter in Python to handle Cyrillic text properly
        filtered_records = []
        for record in all_records:
            # Fields to search: doc_type(1), title(2), sender_branch(4), sender_department(5), sender_fio(7)
            search_fields = [
                str(record[1]).lower() if record[1] else '',  # doc_type
                str(record[2]).lower() if record[2] else '',  # title
                str(record[4]).lower() if record[4] else '',  # sender_branch
                str(record[5]).lower() if record[5] else '',  # sender_department
                str(record[7]).lower() if record[7] else '',  # sender_fio
            ]
            
            if any(search_term in field for field in search_fields):
                filtered_records.append(record)
        
        self.documents_table.setRowCount(len(filtered_records))
        
        for row_idx, record in enumerate(filtered_records):
            for col_idx, value in enumerate(record):
                item = QTableWidgetItem(str(value) if value else "")
                self.documents_table.setItem(row_idx, col_idx, item)
        
        conn.close()
    
    def add_document(self):
        """Add new document"""
        dialog = DocumentDialog(self.main_app)
        if dialog.exec_() == QDialog.Accepted:
            self.load_documents()
    
    def edit_document(self):
        """Edit selected document"""
        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите документ для редактирования")
            return
        
        doc_id_item = self.documents_table.item(current_row, 0)
        if doc_id_item:
            doc_id = int(doc_id_item.text())
            dialog = DocumentDialog(self.main_app, doc_id)
            if dialog.exec_() == QDialog.Accepted:
                self.load_documents()
    
    def delete_document(self):
        """Delete selected document"""
        current_row = self.documents_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите документ для удаления")
            return
        
        doc_id_item = self.documents_table.item(current_row, 0)
        if doc_id_item:
            doc_id = int(doc_id_item.text())
            
            reply = QMessageBox.question(
                self, 
                "Подтверждение", 
                "Вы уверены, что хотите удалить выбранный документ?",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                conn = sqlite3.connect(self.main_app.db_path)
                cursor = conn.cursor()
                
                # Get file path to remove the actual file
                cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
                result = cursor.fetchone()
                if result and result[0]:
                    try:
                        os.remove(result[0])
                    except OSError:
                        pass  # File might not exist
                
                # Delete from database
                cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
                conn.commit()
                conn.close()
                
                self.load_documents()


class DocumentDialog(QDialog):
    def __init__(self, main_app, doc_id=None):
        super().__init__()
        self.main_app = main_app
        self.doc_id = doc_id
        self.setWindowTitle("Документ" if doc_id else "Новый документ")
        self.setGeometry(200, 200, 600, 700)
        
        self.init_ui()
        if doc_id:
            self.load_document_data()
    
    def init_ui(self):
        """Initialize document dialog UI"""
        layout = QVBoxLayout()
        
        # Form layout for document properties
        form_layout = QFormLayout()
        
        # Document type
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems(["Основной", "Дополнительный", "Отчетный", "Прочий"])
        form_layout.addRow("Тип документа:", self.doc_type_combo)
        
        # Title
        self.title_edit = QLineEdit()
        form_layout.addRow("Наименование:", self.title_edit)
        
        # Description
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(100)
        form_layout.addRow("Описание:", self.description_edit)
        
        # Sender branch
        self.sender_branch_edit = QLineEdit()
        form_layout.addRow("Филиал отправителя:", self.sender_branch_edit)
        
        # Sender department
        self.sender_dept_edit = QLineEdit()
        form_layout.addRow("Отдел отправителя:", self.sender_dept_edit)
        
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
        self.evaluation_combo.addItems(["", "Отлично", "Хорошо", "Удовлетворительно", "Неудовлетворительно"])
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
        self.status_combo.addItems(["Отправлен", "Получен", "На оценке", "Оценен", "Архив"])
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
        """Save document to database"""
        # Validate required fields
        if not self.title_edit.text():
            QMessageBox.warning(self, "Ошибка", "Введите наименование документа")
            return
        
        if not self.sender_branch_edit.text():
            QMessageBox.warning(self, "Ошибка", "Введите филиал отправителя")
            return
        
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        # Prepare data
        doc_data = (
            self.doc_type_combo.currentText(),
            self.title_edit.text(),
            self.description_edit.toPlainText(),
            self.sender_branch_edit.text(),
            self.sender_dept_edit.text(),
            self.sender_pos_edit.text(),
            self.sender_fio_edit.text(),
            self.outgoing_number_edit.text(),
            self.outgoing_date_edit.date().toString("yyyy-MM-dd"),
            self.incoming_number_edit.text(),
            self.incoming_date_edit.date().toString("yyyy-MM-dd"),
            self.evaluator_edit.text(),
            self.evaluation_combo.currentText(),
            self.evaluation_date_edit.date().toString("yyyy-MM-dd"),
            self.file_path_edit.text(),
            self.status_combo.currentText()
        )
        
        if self.doc_id:
            # Update existing document
            cursor.execute('''
                UPDATE documents 
                SET doc_type=?, title=?, description=?, sender_branch=?, 
                    sender_department=?, sender_position=?, sender_fio=?, 
                    outgoing_number=?, outgoing_date=?, incoming_number=?, 
                    incoming_date=?, evaluator=?, evaluation=?, 
                    evaluation_date=?, file_path=?, status=?
                WHERE id=?
            ''', doc_data + (self.doc_id,))
        else:
            # Insert new document
            cursor.execute('''
                INSERT INTO documents (
                    doc_type, title, description, sender_branch, 
                    sender_department, sender_position, sender_fio, 
                    outgoing_number, outgoing_date, incoming_number, 
                    incoming_date, evaluator, evaluation, 
                    evaluation_date, file_path, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', doc_data)
        
        conn.commit()
        conn.close()
        
        self.accept()
    
    def load_document_data(self):
        """Load existing document data for editing"""
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (self.doc_id,))
        record = cursor.fetchone()
        conn.close()
        
        if record:
            self.doc_type_combo.setCurrentText(record[1])
            self.title_edit.setText(record[2])
            self.description_edit.setPlainText(record[3] or "")
            self.sender_branch_edit.setText(record[4])
            self.sender_dept_edit.setText(record[5])
            self.sender_pos_edit.setText(record[6])
            self.sender_fio_edit.setText(record[7])
            self.outgoing_number_edit.setText(record[8])
            if record[9]:  # outgoing_date
                self.outgoing_date_edit.setDate(QDate.fromString(record[9], "yyyy-MM-dd"))
            self.incoming_number_edit.setText(record[10])
            if record[11]:  # incoming_date
                self.incoming_date_edit.setDate(QDate.fromString(record[11], "yyyy-MM-dd"))
            self.evaluator_edit.setText(record[12])
            self.evaluation_combo.setCurrentText(record[13] or "")
            if record[14]:  # evaluation_date
                self.evaluation_date_edit.setDate(QDate.fromString(record[14], "yyyy-MM-dd"))
            self.file_path_edit.setText(record[15] or "")
            self.status_combo.setCurrentText(record[16] or "")


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
        self.branch_filter.addItem("Все филиалы")
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
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM branches")
        branches = cursor.fetchall()
        
        for branch in branches:
            self.branch_filter.addItem(branch[0])
        
        conn.close()
    
    def generate_statistics(self):
        """Generate statistics based on filters"""
        selected_branch = self.branch_filter.currentText()
        period = self.period_combo.currentText()
        
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        # Base query
        query = "SELECT * FROM documents"
        params = []
        
        if selected_branch != "Все филиалы":
            query += " WHERE sender_branch = ?"
            params.append(selected_branch)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Calculate statistics
        total_docs = len(records)
        
        # Count by evaluation
        eval_counts = {"Отлично": 0, "Хорошо": 0, "Удовлетворительно": 0, "Неудовлетворительно": 0, "Без оценки": 0}
        for record in records:
            evaluation = record[13]  # evaluation column
            if evaluation:
                if evaluation in eval_counts:
                    eval_counts[evaluation] += 1
                else:
                    eval_counts["Без оценки"] += 1
            else:
                eval_counts["Без оценки"] += 1
        
        # Count by status
        status_counts = {}
        for record in records:
            status = record[16]  # status column
            if status:
                status_counts[status] = status_counts.get(status, 0) + 1
            else:
                status_counts["Без статуса"] = status_counts.get("Без статуса", 0) + 1
        
        # Count by department
        dept_counts = {}
        for record in records:
            dept = record[5]  # sender_department column
            if dept:
                dept_counts[dept] = dept_counts.get(dept, 0) + 1
            else:
                dept_counts["Без отдела"] = dept_counts.get("Без отдела", 0) + 1
        
        # Format statistics
        stats_text = f"""Статистика по документам
Фильтр: {selected_branch}, Период: {period}

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
        conn.close()


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
        self.export_branch.addItem("Все филиалы")
        
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM branches")
        branches = cursor.fetchall()
        
        for branch in branches:
            self.export_branch.addItem(branch[0])
        
        conn.close()
    
    def export_documents(self):
        """Export documents to ZIP archive"""
        selected_branch = self.export_branch.currentText()
        
        conn = sqlite3.connect(self.main_app.db_path)
        cursor = conn.cursor()
        
        # Query documents
        query = "SELECT * FROM documents"
        params = []
        
        if selected_branch != "Все филиалы":
            query += " WHERE sender_branch = ?"
            params.append(selected_branch)
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        # Create export data
        export_data = {
            "export_date": datetime.now().isoformat(),
            "source_branch": selected_branch,
            "documents": []
        }
        
        for record in records:
            doc_dict = {
                "id": record[0],
                "doc_type": record[1],
                "title": record[2],
                "description": record[3],
                "sender_branch": record[4],
                "sender_department": record[5],
                "sender_position": record[6],
                "sender_fio": record[7],
                "outgoing_number": record[8],
                "outgoing_date": record[9],
                "incoming_number": record[10],
                "incoming_date": record[11],
                "evaluator": record[12],
                "evaluation": record[13],
                "evaluation_date": record[14],
                "file_path": record[15],
                "status": record[16],
                "created_at": record[17]
            }
            export_data["documents"].append(doc_dict)
        
        conn.close()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"export_{selected_branch.replace(' ', '_')}_{timestamp}.zip"
        
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