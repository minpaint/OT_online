# 📁 directory/admin/__init__.py

from django.contrib import admin  # noqa: F401

# Импорт админ-классов (они регистрируются через декораторы @admin.register)
from .department import DepartmentAdmin
from .document import DocumentAdmin
from .employee import EmployeeAdmin
from .equipment import EquipmentAdmin
from .organization import OrganizationAdmin
from .position import PositionAdmin
from .subdivision import StructuralSubdivisionAdmin
