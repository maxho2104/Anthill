"""
Peewee ORM Models for Document Workflow Management System
"""
from peewee import *
from datetime import datetime

# Database initialization
db = SqliteDatabase('documents.db')

class BaseModel(Model):
    class Meta:
        database = db

class Branch(BaseModel):
    """
    Model representing enterprise branches
    """
    name = CharField(unique=True, verbose_name="Название филиала")
    address = TextField(null=True, verbose_name="Адрес")
    contact_person = CharField(null=True, verbose_name="Контактное лицо")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'branches'

    def __str__(self):
        return self.name

class Department(BaseModel):
    """
    Model representing departments in branches
    """
    name = CharField(verbose_name="Название отдела")
    branch = ForeignKeyField(Branch, backref='departments', verbose_name="Филиал")
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'departments'
        indexes = (
            (('name', 'branch'), True),  # Unique constraint on name and branch
        )

    def __str__(self):
        return f"{self.name} ({self.branch.name})"

class Document(BaseModel):
    """
    Model representing documents in the workflow system
    """
    DOCUMENT_TYPES = (
        ('main', 'Основной'),
        ('additional', 'Дополнительный'),
        ('report', 'Отчетный'),
        ('other', 'Прочий')
    )
    
    EVALUATIONS = (
        ('excellent', 'Отлично'),
        ('good', 'Хорошо'),
        ('satisfactory', 'Удовлетворительно'),
        ('unsatisfactory', 'Неудовлетворительно')
    )
    
    STATUSES = (
        ('sent', 'Отправлен'),
        ('received', 'Получен'),
        ('evaluating', 'На оценке'),
        ('evaluated', 'Оценен'),
        ('archived', 'Архив')
    )
    
    doc_type = CharField(max_length=20, choices=DOCUMENT_TYPES, verbose_name="Тип документа")
    title = CharField(max_length=500, verbose_name="Наименование")
    description = TextField(null=True, verbose_name="Описание")
    
    # Sender information
    sender_branch = ForeignKeyField(Branch, verbose_name="Филиал отправителя")
    sender_department = ForeignKeyField(Department, null=True, verbose_name="Отдел отправителя")
    sender_position = CharField(max_length=200, null=True, verbose_name="Должность отправителя")
    sender_fio = CharField(max_length=300, verbose_name="ФИО отправителя")
    
    # Document numbers and dates
    outgoing_number = CharField(max_length=50, null=True, verbose_name="Исходящий номер")
    outgoing_date = DateField(null=True, verbose_name="Дата отправки")
    incoming_number = CharField(max_length=50, null=True, verbose_name="Входящий номер")
    incoming_date = DateField(null=True, verbose_name="Дата получения")
    
    # Evaluation information
    evaluator = CharField(max_length=300, null=True, verbose_name="Оценивающий")
    evaluation = CharField(max_length=20, choices=EVALUATIONS, null=True, verbose_name="Оценка")
    evaluation_date = DateField(null=True, verbose_name="Дата оценки")
    
    # File path
    file_path = CharField(max_length=1000, null=True, verbose_name="Путь к файлу")
    
    # Status and timestamps
    status = CharField(max_length=20, choices=STATUSES, default='sent', verbose_name="Статус")
    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'documents'
        indexes = (
            (('outgoing_number', 'outgoing_date'), False),  # Non-unique index
        )

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super(Document, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} [{self.doc_type}]"

def initialize_db():
    """Initialize the database with required tables"""
    db.connect()
    db.create_tables([Branch, Department, Document], safe=True)
    return db