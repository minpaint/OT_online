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
from django.utils.html import format_html
from directory.models import EmployeeHiring
from .medical_examination import *
from .quiz_admin import *  # Импортируем админку экзаменов


__all__ = [
    'DepartmentAdmin',
    'DocumentAdmin',
    'EmployeeAdmin',
    'EquipmentAdmin',
    'OrganizationAdmin',
    'PositionAdmin',
    'StructuralSubdivisionAdmin',
    'CustomUserAdmin',
    'EmployeeHiringAdmin',  # Добавляем в список экспорта
]


@admin.register(EmployeeHiring)
class EmployeeHiringAdmin(admin.ModelAdmin):
    list_display = ['employee_name', 'hiring_type_display', 'hiring_date', 'organization_display', 'position_display',
                    'documents_count', 'is_active']
    list_filter = ['is_active', 'hiring_type', 'hiring_date', 'organization']
    search_fields = ['employee__full_name_nominative', 'position__position_name']
    date_hierarchy = 'hiring_date'
    filter_horizontal = ['documents']

    fieldsets = [
        (None, {'fields': ['employee', 'hiring_type', 'hiring_date', 'start_date', 'is_active']}),
        ('Организационная структура', {'fields': ['organization', 'subdivision', 'department', 'position']}),
        ('Документы', {'fields': ['documents']}),
        ('Дополнительно', {'fields': ['notes']}),
    ]

    def employee_name(self, obj):
        return obj.employee.full_name_nominative

    employee_name.short_description = 'Сотрудник'

    def hiring_type_display(self, obj):
        return obj.get_hiring_type_display()

    hiring_type_display.short_description = 'Вид приема'

    def organization_display(self, obj):
        return obj.organization.short_name_ru

    organization_display.short_description = 'Организация'

    def position_display(self, obj):
        return obj.position.position_name

    position_display.short_description = 'Должность'

    def documents_count(self, obj):
        count = obj.documents.count()
        if count:
            return format_html('<span class="badge badge-primary">{}</span>', count)
        return format_html('<span class="badge badge-secondary">0</span>')

    documents_count.short_description = 'Документы'
