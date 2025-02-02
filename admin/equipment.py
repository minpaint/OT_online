from django.contrib import admin
from directory.models.equipment import Equipment

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    list_display = [
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']
    autocomplete_fields = ['organization']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'subdivision', 'department'
        )