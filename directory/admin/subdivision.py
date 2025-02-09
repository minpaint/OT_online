from django.contrib import admin
from directory.models.subdivision import StructuralSubdivision
from mptt.admin import MPTTModelAdmin
from directory.forms import StructuralSubdivisionForm

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(MPTTModelAdmin):
    """
    🏭 Админ-класс для модели StructuralSubdivision.
    Отображает подразделения с фильтрацией по организации.
    """
    form = StructuralSubdivisionForm
    mptt_indent_field = "name"
    list_display = ('indented_title_display', 'organization',)
    list_display_links = ('indented_title_display',)
    list_filter = ['organization']
    search_fields = ['name', 'short_name']

    def indented_title_display(self, obj):
        """
        🔍 Формирует отступлённое название, отражающее уровень вложенности.
        """
        indent = "&nbsp;" * (obj.level * 4)  # 4 неразрывных пробела на уровень
        return admin.utils.format_html("{}{}", indent, obj.name)

    indented_title_display.short_description = "Наименование подразделения"

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')