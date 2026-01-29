"""
TableModel for displaying documents in QTableView with lazy loading
"""
from PyQt5.QtCore import QAbstractTableModel, Qt, QModelIndex
from ..Classes import Document, Branch, Department
from datetime import datetime


class DocumentTableModel(QAbstractTableModel):
    """
    Table model for displaying documents with lazy loading capability
    Supports large datasets by loading N records at a time
    """
    
    def __init__(self, batch_size=100, parent=None):
        super().__init__(parent)
        self.batch_size = batch_size
        self.data_list = []
        self.total_count = 0
        self.all_loaded = False
        self.filters = {}
        
        # Define column headers
        self.headers = [
            "ID", 
            "Тип", 
            "Наименование", 
            "Филиал", 
            "Отдел", 
            "Отправитель", 
            "Исх. №", 
            "Исх. дата", 
            "Вх. №", 
            "Вх. дата", 
            "Оценка", 
            "Статус"
        ]
        
        # Define corresponding model fields
        self.field_mapping = [
            'id',
            'doc_type',
            'title',
            'sender_branch.name',  # Need to join with Branch
            'sender_department.name',  # Need to join with Department
            'sender_fio',
            'outgoing_number',
            'outgoing_date',
            'incoming_number',
            'incoming_date',
            'evaluation',
            'status'
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self.data_list)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.data_list):
            return None

        if role == Qt.DisplayRole:
            doc = self.data_list[index.row()]
            field = self.field_mapping[index.column()]
            
            # Handle nested attributes (like branch.name)
            if '.' in field:
                parts = field.split('.')
                value = getattr(doc, parts[0])
                if value is not None:
                    for part in parts[1:]:
                        value = getattr(value, part)
                return str(value) if value is not None else ""
            else:
                value = getattr(doc, field)
                if value is None:
                    return ""
                elif isinstance(value, datetime):
                    return value.strftime("%Y-%m-%d")
                else:
                    # Convert enum values to their display names
                    if field == 'doc_type':
                        doc_type_map = dict(Document.DOCUMENT_TYPES)
                        return doc_type_map.get(value, value)
                    elif field == 'evaluation':
                        eval_map = dict(Document.EVALUATIONS)
                        return eval_map.get(value, value)
                    elif field == 'status':
                        status_map = dict(Document.STATUSES)
                        return status_map.get(value, value)
                    else:
                        return str(value)
        
        elif role == Qt.EditRole:
            doc = self.data_list[index.row()]
            field = self.field_mapping[index.column()]
            
            if '.' in field:
                parts = field.split('.')
                value = getattr(doc, parts[0])
                if value is not None:
                    for part in parts[1:]:
                        value = getattr(value, part)
                return str(value) if value is not None else ""
            else:
                value = getattr(doc, field)
                return value

        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if section < len(self.headers):
                return self.headers[section]
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def load_data(self, offset=0, filters=None):
        """
        Load data with pagination and optional filters
        """
        if filters is not None:
            self.filters = filters
        
        # Build query with joins and filters
        query = (Document
                 .select(Document, Branch, Department)
                 .join(Branch, on=(Document.sender_branch == Branch.id))
                 .switch(Document)  # Switch back to Document to join Department
                 .join(Department, on=(Document.sender_department == Department.id), attr='sender_department_rel')
                 .order_by(Document.created_at.desc()))

        # Apply filters if any
        if self.filters:
            for field, value in self.filters.items():
                if value:
                    if field == 'search_term':
                        query = query.where(
                            (Document.title.contains(value)) |
                            (Document.sender_fio.contains(value)) |
                            (Document.outgoing_number.contains(value)) |
                            (Branch.name.contains(value))
                        )
                    elif field == 'doc_type':
                        query = query.where(Document.doc_type == value)
                    elif field == 'status':
                        query = query.where(Document.status == value)
                    elif field == 'branch_id':
                        query = query.where(Document.sender_branch == value)
                    elif field == 'date_from':
                        from datetime import datetime
                        date_from = datetime.strptime(value, '%Y-%m-%d').date()
                        query = query.where(Document.outgoing_date >= date_from)
                    elif field == 'date_to':
                        from datetime import datetime
                        date_to = datetime.strptime(value, '%Y-%m-%d').date()
                        query = query.where(Document.outgoing_date <= date_to)

        # Count total records for this query
        self.total_count = query.count()

        # Apply pagination
        query = query.offset(offset).limit(self.batch_size)
        
        # Fetch data
        new_data = list(query)
        self.data_list.extend(new_data)
        
        # Check if all records are loaded
        if len(self.data_list) >= self.total_count:
            self.all_loaded = True

        # Emit data changed signal
        self.layoutChanged.emit()

    def clear_data(self):
        """Clear all loaded data"""
        self.data_list.clear()
        self.all_loaded = False
        self.layoutChanged.emit()

    def can_fetch_more(self, parent=QModelIndex()):
        """Check if more data can be fetched"""
        return not self.all_loaded

    def fetch_more(self, parent=QModelIndex()):
        """Fetch more data when needed"""
        if self.all_loaded:
            return

        remainder = self.total_count - len(self.data_list)
        items_to_fetch = min(remainder, self.batch_size)

        if items_to_fetch <= 0:
            self.all_loaded = True
            return

        self.beginInsertRows(QModelIndex(), len(self.data_list), len(self.data_list) + items_to_fetch - 1)
        
        # Calculate offset for next batch
        offset = len(self.data_list)
        # Build query with joins and filters
        query = (Document
                 .select(Document, Branch, Department)
                 .join(Branch, on=(Document.sender_branch == Branch.id))
                 .switch(Document)  # Switch back to Document to join Department
                 .join(Department, on=(Document.sender_department == Department.id), attr='sender_department_rel')
                 .order_by(Document.created_at.desc()))

        # Apply filters if any
        if self.filters:
            for field, value in self.filters.items():
                if value:
                    if field == 'search_term':
                        query = query.where(
                            (Document.title.contains(value)) |
                            (Document.sender_fio.contains(value)) |
                            (Document.outgoing_number.contains(value)) |
                            (Branch.name.contains(value))
                        )
                    elif field == 'doc_type':
                        query = query.where(Document.doc_type == value)
                    elif field == 'status':
                        query = query.where(Document.status == value)
                    elif field == 'branch_id':
                        query = query.where(Document.sender_branch == value)
                    elif field == 'date_from':
                        from datetime import datetime
                        date_from = datetime.strptime(value, '%Y-%m-%d').date()
                        query = query.where(Document.outgoing_date >= date_from)
                    elif field == 'date_to':
                        from datetime import datetime
                        date_to = datetime.strptime(value, '%Y-%m-%d').date()
                        query = query.where(Document.outgoing_date <= date_to)

        # Apply pagination
        query = query.offset(offset).limit(items_to_fetch)
        
        # Fetch data
        new_data = list(query)
        self.data_list.extend(new_data)
        
        # Check if all records are loaded
        if len(self.data_list) >= self.total_count:
            self.all_loaded = True

        self.endInsertRows()