from django.contrib import admin
from directory.models.position import Position
from directory.forms import PositionForm

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    👔 Админ-класс для модели Position.
    """
    form = PositionForm
    list_display = [
        'position_name',
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'can_be_internship_leader'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'can_be_internship_leader'
    ]
    search_fields = ['position_name', 'safety_instructions_numbers']
    filter_horizontal = ['documents', 'equipment']
    fieldsets = (
        (None, {'fields': ('position_name',)}),
        ('Организационная структура', {'fields': ('organization', 'subdivision', 'department')}),
        ('Безопасность', {'fields': (
            'safety_instructions_numbers',
            'electrical_safety_group',
            'internship_period_days',
            'is_responsible_for_safety',
            'is_electrical_personnel',
            'can_be_internship_leader'
        )}),
        ('Связанные документы и оборудование', {'fields': ('documents', 'equipment'), 'classes': ('collapse',)}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        ).prefetch_related('documents', 'equipment')