# 📁 directory/admin/employee.py
from django.contrib import admin  # 🛠️ Импорт админки Django
from directory.models.employee import Employee  # 👤 Импорт модели Employee

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee (Сотрудник).

    Иерархия зависимых полей:
      1️⃣ Организация – обязательное поле.
      2️⃣ Подразделение – опциональное, должно принадлежать выбранной организации.
      3️⃣ Отдел – опциональное, должно принадлежать выбранному подразделению.
    """
    list_display = [
        'full_name_nominative',
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor',
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor',
        'clothing_size',
        'shoe_size',
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]

    fieldsets = (
        ('👤 Персональные данные', {
            'fields': (
                'full_name_nominative',
                'full_name_dative',
                'date_of_birth',
                'place_of_residence'
            )
        }),
        ('🏢 Организационная структура', {
            'fields': (
                'organization',
                'subdivision',
                'department',
                'position',
                'is_contractor'
            )
        }),
        ('👕 Спецодежда', {
            'fields': (
                'height',
                'clothing_size',
                'shoe_size'
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """
        ⚡️ Оптимизация запросов с помощью select_related.
        """
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'subdivision', 'department', 'position')
