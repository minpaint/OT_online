# 📁 directory/admin/position.py
from django.contrib import admin  # 🛠️ Импорт админки Django
from directory.models.position import Position  # 👔 Импорт модели Position

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Position (Должность).
    Отображает должности с фильтрацией по организации, подразделению и отделу.
    Новое поле: "Может быть руководителем стажировки".
    """
    list_display = [
        'position_name',
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'is_responsible_for_safety',
        'is_electrical_personnel',
        'can_be_internship_leader'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'electrical_safety_group',
        'is_responsible_for_safety',
        'is_electrical_personnel',
        'can_be_internship_leader'
    ]
    search_fields = ['position_name', 'safety_instructions_numbers']
    filter_horizontal = ['documents', 'equipment']

    fieldsets = (
        (None, {'fields': ('position_name',)}),
        ('Принадлежность', {'fields': ('organization', 'subdivision', 'department')}),
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
        """
        ⚡️ Оптимизация запросов с помощью select_related и prefetch_related.
        """
        qs = super().get_queryset(request)
        return qs.select_related('organization', 'subdivision', 'department')\
                 .prefetch_related('documents', 'equipment')
