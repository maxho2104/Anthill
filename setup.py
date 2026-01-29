"""
Setup script for Document Workflow Management Application
"""
from setuptools import setup, find_packages

setup(
    name="document-workflow-app",
    version="1.0.0",
    description="Application for managing internal correspondence between headquarters and branches",
    author="Enterprise Documentation System",
    packages=find_packages(),
    install_requires=[
        "PyQt5>=5.15.0",
        "peewee>=3.14.0",
    ],
    entry_points={
        'console_scripts': [
            'document-workflow-app=main:main',
        ],
    },
)