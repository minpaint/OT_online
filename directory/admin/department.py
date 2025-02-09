# 📁 directory/admin/department.py
from django.contrib import admin  # 🛠️ Импорт стандартной админки Django
from directory.models.department import Department  # 📂 Импорт модели Department

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Department.
    Отображает отделы с фильтрацией по организации и подразделению.
    """
    list_display = ['name', 'short_name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name', 'short_name']

    fieldsets = (
        (None, {
            'fields': ('name', 'short_name', 'organization', 'subdivision')
        }),
    )

    def get_queryset(self, request):
        """
        ⚡️ Оптимизация запросов с использованием select_related.
        """
        return super().get_queryset(request).select_related('organization', 'subdivision')
