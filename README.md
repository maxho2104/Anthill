# Document Workflow Management Application

This application automates the activities of enterprise documentation staff for accounting of internal correspondence between headquarters and branches.

## Features

- **Document Management**: Full CRUD operations for documents with support for various document types
- **Peewee ORM Integration**: Uses Peewee ORM with SQLite database backend
- **Lazy Loading**: Efficient handling of large datasets (30,000+ records) with pagination
- **Advanced Filtering**: Comprehensive filtering options with date ranges
- **QTableView Integration**: Efficient display of documents with custom table model
- **Export/Import**: ZIP-based export/import functionality for inter-office communication
- **Statistics**: Automated statistical calculations and reporting
- **Search**: Fast search across document fields

## Architecture

- **Frontend**: PyQt5 GUI
- **Backend**: Peewee ORM with SQLite
- **File Storage**: Structured file storage (files stored on disk, references in DB)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

## Usage

1. **Documents Tab**: View, add, edit, and delete documents with filtering capabilities
2. **Statistics Tab**: Generate statistical reports by branch, department, and time period
3. **Export/Import Tab**: Exchange documents and evaluations between branches and headquarters

## Key Components

- `Peewee/Classes/`: Contains Peewee models and custom components
- `DocumentTableModel`: Custom QAbstractTableModel with lazy loading
- `FilterDialog`: Advanced filtering options
- `test_data.py`: Generator for test data with Faker library

## Building

To create a standalone executable:
```bash
python build_app.py
```

## Database Schema

The application uses three main tables:
- `branches`: Enterprise branches
- `departments`: Departments within branches
- `documents`: Document records with metadata

## Lazy Loading

The application implements efficient lazy loading with configurable batch sizes to handle large datasets without performance degradation.

## Advanced Features

- **Filter Dialog**: Provides comprehensive filtering by document type, status, branch, and date range
- **Context Menu**: Right-click context menu for quick document operations
- **Double-click Editing**: Edit documents with double-click on table rows
- **Row Selection**: Entire row highlighting and selection