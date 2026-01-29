"""
Test data generator for Document Workflow Management System
Uses Faker to populate the database with realistic test data
"""
from faker import Faker
from faker.providers import company, person, internet, date_time
from random import choice, randint
from datetime import datetime, timedelta
import os
from ..Classes import Branch, Department, Document, initialize_db


def generate_test_data(count=50000):
    """
    Generate test data for the system
    Creates branches, departments, and documents
    """
    fake = Faker('ru_RU')  # Russian locale for realistic data
    
    print("Initializing database...")
    db = initialize_db()
    
    print("Generating test data...")
    
    # Create some branches
    print("Creating branches...")
    branches = []
    branch_names = [
        "Московский филиал", "Петербургский филиал", "Новосибирский филиал",
        "Екатеринбургский филиал", "Казанский филиал", "Нижегородский филиал",
        "Челябинский филиал", "Самарский филиал", "Омский филиал", "Ростовский филиал"
    ]
    
    for name in branch_names:
        branch, created = Branch.get_or_create(
            name=name,
            defaults={
                'address': fake.address(),
                'contact_person': fake.name()
            }
        )
        branches.append(branch)
        print(f"Created branch: {branch.name}")
    
    # Create departments for each branch
    print("Creating departments...")
    departments = []
    dept_names = [
        "Отдел кадров", "Бухгалтерия", "IT-отдел", "Отдел продаж", 
        "Отдел маркетинга", "Юридический отдел", "Отдел логистики",
        "Отдел закупок", "Производственный отдел", "Отдел качества"
    ]
    
    for branch in branches:
        for dept_name in dept_names:
            dept, created = Department.get_or_create(
                name=dept_name,
                branch=branch,
                defaults={}
            )
            departments.append(dept)
    
    print(f"Created {len(departments)} departments")
    
    # Generate documents in batches to avoid memory issues
    batch_size = 1000
    generated_count = 0
    
    print(f"Generating {count} documents...")
    
    while generated_count < count:
        current_batch = min(batch_size, count - generated_count)
        batch_docs = []
        
        for i in range(current_batch):
            # Select random related objects
            branch = choice(branches)
            dept = choice([d for d in departments if d.branch == branch])  # Dept from same branch
            
            # Create document
            doc = Document.create(
                doc_type=choice(['main', 'additional', 'report', 'other']),
                title=fake.catch_phrase(),
                description=fake.text(max_nb_chars=200),
                sender_branch=branch,
                sender_department=dept,
                sender_position=fake.job(),
                sender_fio=fake.name(),
                outgoing_number=f"{randint(1, 9999)}/{fake.year()}",
                outgoing_date=fake.date_between(start_date='-2y', end_date='today'),
                incoming_number=f"{randint(1, 9999)}/{fake.year()}" if randint(0, 1) else None,
                incoming_date=fake.date_between(start_date='-2y', end_date='today') if randint(0, 1) else None,
                evaluator=fake.name() if randint(0, 1) else None,
                evaluation=choice(['excellent', 'good', 'satisfactory', 'unsatisfactory']) if randint(0, 1) else None,
                evaluation_date=fake.date_between(start_date='-2y', end_date='today') if randint(0, 1) else None,
                file_path=f"document_storage/sample_{generated_count + i + 1}.pdf" if randint(0, 1) else None,
                status=choice(['sent', 'received', 'evaluating', 'evaluated', 'archived'])
            )
            batch_docs.append(doc)
        
        generated_count += current_batch
        print(f"Generated {generated_count}/{count} documents")
    
    print(f"Successfully generated {generated_count} documents")
    
    # Create sample storage directory
    if not os.path.exists('document_storage'):
        os.makedirs('document_storage')
    
    print("Test data generation completed!")


if __name__ == "__main__":
    generate_test_data(5000)  # Generate smaller set for testing