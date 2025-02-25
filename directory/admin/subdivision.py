"""
🏭 Admin для структурного подразделения без MPTT.
Отображает древовидное представление подразделений.
Использует универсальный миксин TreeViewMixin.
"""
from django.contrib import admin
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models import StructuralSubdivision
from directory.forms.subdivision import StructuralSubdivisionForm

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    🏭 Админ-класс для модели StructuralSubdivision.
    Отображает древовидное представление: Организация → Подразделение.
    """
    form = StructuralSubdivisionForm

    # Используем шаблон, специфичный для структурных подразделений
    change_list_template = "admin/directory/subdivision/change_list_tree.html"

    # ⚙️ Настройки дерева: здесь ключевой параметр model_name определяет, что URL будет формироваться как
    # 'admin:directory_structuralsubdivision_change'
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'no_subdivision': '🏗️',
            # Для подразделения уровней "department" и "item" не используются, поэтому можно задать любую иконку:
            'department': '📂',
            'item': '🏭',
        },
        'fields': {
            'name_field': 'name',                # Имя подразделения
            'organization_field': 'organization',# FK на Organization
            'subdivision_field': None,             # Нет вложенных подразделений
            'department_field': None,              # Нет уровня "отдел"
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        },
        # 🔑 Ключевой параметр: правильное имя модели для формирования URL
        'model_name': 'structuralsubdivision'
    }

    list_display = ['name', 'short_name', 'organization']
    list_filter = ['organization']
    search_fields = ['name', 'short_name']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs
