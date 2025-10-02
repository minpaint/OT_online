"""
📊 Ресурсы для импорта/экспорта данных через django-import-export
"""
from .organization_structure import OrganizationStructureResource
from .employee import EmployeeResource

__all__ = [
    'OrganizationStructureResource',
    'EmployeeResource',
]