# directory/models/__init__.py
from .organization import Organization
from .subdivision import StructuralSubdivision
from .department import Department
from .document import Document
from .equipment import Equipment
from .position import Position
from .employee import Employee
from .profile import Profile
from .siz_issued import SIZIssued
from .siz import SIZ, SIZNorm
from .document_template import DocumentTemplate, GeneratedDocument
from .commission import Commission, CommissionMember
from .hiring import EmployeeHiring
# Добавляем импорт медицинских моделей
from .medical_examination import HarmfulFactor, MedicalExaminationType, MedicalSettings
from .medical_norm import MedicalExaminationNorm, PositionMedicalFactor, EmployeeMedicalExamination

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
    'SIZ',
    'SIZNorm',
    'DocumentTemplate',
    'GeneratedDocument',
    'Commission',
    'CommissionMember',
    'EmployeeHiring',
    # Добавляем медицинские модели в список экспорта
    'HarmfulFactor',
    'MedicalExaminationType',
    'MedicalSettings',
    'MedicalExaminationNorm',
    'PositionMedicalFactor',
    'EmployeeMedicalExamination',
]