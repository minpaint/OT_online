# 📁 directory/admin/subdivision.py
from django.contrib import admin  # 🛠️ Импорт админки Django
from mptt.admin import DraggableMPTTAdmin
from directory.models.subdivision import StructuralSubdivision

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(DraggableMPTTAdmin):
    """
    🏭 Админ-класс для модели StructuralSubdivision.
    Отображает подразделения в виде дерева с фильтрацией по организации.
    """
    mptt_indent_field = "name"
    list_display = ('tree_actions', 'indented_title', 'organization')
    list_display_links = ('indented_title',)
