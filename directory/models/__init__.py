# 📁 directory/models/__init__.py

# Импортируем модели в правильном порядке
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment
from .position import Position
from .employee import Employee

__all__ = [
    'Organization',
    'StructuralSubdivision',
    'Department',
    'Document',
    'Equipment',
    'Position',
    'Employee',
]