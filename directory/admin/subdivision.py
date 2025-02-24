"""
🏭 Admin для подразделения без MPTT.
"""
from django.contrib import admin
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models import StructuralSubdivision
from directory.forms.subdivision import StructuralSubdivisionForm

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    🏭 Тот же древовидный вывод:
    Организация -> (Подразделение)
    """
    form = StructuralSubdivisionForm

    # 🏷️ Используем наш шаблон
    change_list_template = "admin/directory/subdivision/change_list_tree.html"

    # ⚙️ Настройки
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'no_subdivision': '🏗️',  # Можно не использовать
            'department': '📂',      # Можно не использовать
            'item': '🏭',           # Иконка для "листьев" - но здесь листья = сами Subdivision?
        },
        'fields': {
            'name_field': 'name',
            'organization_field': 'organization',
            'subdivision_field': None,  # У нас нет вложенных субподразделений
            'department_field': None,
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    list_display = ['name', 'short_name', 'organization']
    search_fields = ['name', 'short_name']
    list_filter = ['organization']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs
