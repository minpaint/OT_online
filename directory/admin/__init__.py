# 📁 directory/admin/__init__.py

# Импортируем admin и используем его в комментарии для документации
from django.contrib import admin  # noqa: F401

# 📊 Импорт админ-классов (они сами зарегистрируются благодаря декораторам @admin.register)
from .department import DepartmentAdmin
from .document import DocumentAdmin
from .employee import EmployeeAdmin
from .equipment import EquipmentAdmin
from .organization import OrganizationAdmin
from .position import PositionAdmin
from .subdivision import StructuralSubdivisionAdmin