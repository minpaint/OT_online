from django.contrib import admin
from deadline_control.models import MedicalReferral


@admin.register(MedicalReferral)
class MedicalReferralAdmin(admin.ModelAdmin):
    """
    📋 Администрирование направлений на медосмотр.
    """
    list_display = [
        'id',
        'employee',
        'get_organization',
        'issue_date',
        'issued_by',
        'get_factors_count',
        'has_document'
    ]
    list_filter = [
        'issue_date',
        'employee__organization',
        'issued_by'
    ]
    search_fields = [
        'employee__full_name_nominative',
        'employee_address'
    ]
    date_hierarchy = 'issue_date'
    readonly_fields = [
        'created_at',
        'updated_at',
        'get_factors_list'
    ]
    filter_horizontal = ['harmful_factors']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'employee',
                'issue_date',
                'issued_by'
            )
        }),
        ('Данные на момент выдачи', {
            'fields': (
                'employee_birth_date',
                'employee_address'
            )
        }),
        ('Вредные факторы', {
            'fields': (
                'harmful_factors',
                'get_factors_list'
            )
        }),
        ('Документ', {
            'fields': (
                'document',
                'notes'
            )
        }),
        ('Служебная информация', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def get_organization(self, obj):
        """Возвращает организацию сотрудника"""
        return obj.employee.organization.short_name_ru
    get_organization.short_description = 'Организация'
    get_organization.admin_order_field = 'employee__organization'

    def get_factors_count(self, obj):
        """Количество вредных факторов"""
        return obj.harmful_factors.count()
    get_factors_count.short_description = 'Факторов'

    def has_document(self, obj):
        """Есть ли документ"""
        return bool(obj.document)
    has_document.boolean = True
    has_document.short_description = 'Документ'

    def get_factors_list(self, obj):
        """Список вредных факторов"""
        factors = obj.harmful_factors.all()
        if factors:
            return ', '.join([f"{f.short_name} ({f.full_name})" for f in factors])
        return 'Не указаны'
    get_factors_list.short_description = 'Список факторов'
