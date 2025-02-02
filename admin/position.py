from django.contrib import admin
from directory.models.position import Position


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = [
        'position_name',
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'internship_period_days',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]
    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]
    filter_horizontal = ['documents', 'equipment']
    autocomplete_fields = ['organization']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'subdivision', 'department'
        )