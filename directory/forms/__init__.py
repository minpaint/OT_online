# 📂 directory/forms/__init__.py

from .department import DepartmentForm
from .document import DocumentForm
from .employee import EmployeeForm
from .equipment import EquipmentForm
from .organization import OrganizationForm
from .position import PositionForm
from .subdivision import StructuralSubdivisionForm
from .registration import CustomUserCreationForm
from .employee_hiring import EmployeeHiringForm  # ✅ Добавляем импорт
from .siz_issued import SIZIssueMassForm, SIZIssueReturnForm
from .siz import SIZForm, SIZNormForm

__all__ = [
    "DepartmentForm",
    "DocumentForm",
    "EmployeeForm",
    "EquipmentForm",
    "OrganizationForm",
    "PositionForm",
    "StructuralSubdivisionForm",
    "CustomUserCreationForm",
    "EmployeeHiringForm",  # ✅ Добавляем в список
    "SIZForm",
    "SIZNormForm",
    # 🆕 Добавляем в список экспорта
    "SIZIssueMassForm",
    "SIZIssueReturnForm",
]
