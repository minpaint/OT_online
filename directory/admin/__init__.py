from directory.admin.document_admin import DocumentTemplateAdmin, GeneratedDocumentAdmin
from django.contrib import admin  # noqa: F401
# Импорт админ-классов (они регистрируются через декораторы @admin.register)
from .department import DepartmentAdmin
from .document import DocumentAdmin
from .employee import EmployeeAdmin
from .equipment import EquipmentAdmin
from .organization import OrganizationAdmin
from .position import PositionAdmin
# Вместо файла subdivision_nested импортируем оригинальный файл subdivision.py с MPTTModelAdmin
from .subdivision import StructuralSubdivisionAdmin
from .user import CustomUserAdmin
# Убираем SIZNormGroupAdmin из импортов
from .siz import SIZAdmin, SIZNormAdmin
from .commission_admin import CommissionAdmin

__all__ = [
    'DepartmentAdmin',
    'DocumentAdmin',
    'EmployeeAdmin',
    'EquipmentAdmin',
    'OrganizationAdmin',
    'PositionAdmin',
    'StructuralSubdivisionAdmin',
    'CustomUserAdmin',
]
