# 📁 directory/admin/equipment.py
from django.contrib import admin  # 🛠️ Импорт стандартной админки Django
from directory.models.equipment import Equipment  # ⚙️ Импорт модели Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Equipment (Оборудование).
    Отображает оборудование с фильтрацией по организации, подразделению и отделу.
    """
    list_display = ['equipment_name', 'inventory_number', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']

    fieldsets = (
        (None, {'fields': ('equipment_name', 'inventory_number')}),
        ('Расположение', {'fields': ('organization', 'subdivision', 'department')}),
    )

    def get_queryset(self, request):
        """
        ⚡️ Оптимизация запросов с помощью select_related.
        """
        return super().get_queryset(request).select_related('organization', 'subdivision', 'department')
