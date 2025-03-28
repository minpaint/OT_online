# 📁 directory/models/__init__.py
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment
from .position import Position
from .employee import Employee
from .profile import Profile
from .siz_issued import SIZIssued
from .siz import SIZ, SIZNorm  # 👈 Добавляем импорт моделей SIZ и SIZNorm
# Импортируем модели документов
from .document_template import DocumentTemplate, GeneratedDocument

__all__ = [
    'Organization',
    'Profile',
    'StructuralSubdivision',
    'Department',
    'Document',
    'Equipment',
    'Position',
    'Employee',
    'SIZIssued',
    'SIZ',         # 👈 Добавляем в __all__
    'SIZNorm',     # 👈 Добавляем в __all__
    'DocumentTemplate',  # 👈 Добавляем новую модель шаблонов документов
    'GeneratedDocument', # 👈 Добавляем новую модель сгенерированных документов
]