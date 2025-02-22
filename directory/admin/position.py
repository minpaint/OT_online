"""
👔 Админ-класс для модели Position с древовидным отображением.
Используем кастомный шаблон для вывода change list в виде таблицы.
Логика ограничения по организациям (если не суперпользователь) сохраняется.
"""

from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from directory.models import Position
from directory.forms.position import PositionForm
from directory.admin.mixins.tree_view import TreeViewMixin


@admin.register(Position)
class PositionAdmin(TreeViewMixin, admin.ModelAdmin):
    form = PositionForm

    # Указываем путь к шаблону для древовидного отображения
    change_list_template = "admin/directory/position/change_list_tree.html"

    # Определяем порядок полей в форме
    fieldsets = (
        ('Основная информация', {
            'fields': (
                'position_name',
                'organization',
                'subdivision',
                'department',
                'commission_role',
                'is_responsible_for_safety',
                'can_be_internship_leader',
                'is_electrical_personnel',
            )
        }),
        ('Документация', {
            'fields': (
                'contract_work_name',
                'safety_instructions_numbers',
            )
        }),
        ('Связанные документы и оборудование', {
            'fields': ('documents', 'equipment'),
            'description': '📄 Выберите документы и оборудование, относящиеся к данной должности',
            'classes': ('collapse',)
        }),
    )

    # Фильтры для боковой панели
    list_filter = ['organization', 'subdivision', 'department']

    # Очищаем стандартное отображение столбцов
    list_display = []

    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]

    # Настройки дерева
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'position': '👔',
            'employee': '👤',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'position_name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department'
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    class Media:
        css = {
            'all': ('admin/css/widgets.css',)
        }
        js = [
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
        ]

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Настройка виджетов для полей many-to-many с FilteredSelectMultiple
        """
        if db_field.name == "documents":
            kwargs["widget"] = FilteredSelectMultiple(
                verbose_name="ДОСТУПНЫЕ ДОКУМЕНТЫ",
                is_stacked=False
            )
        if db_field.name == "equipment":
            kwargs["widget"] = FilteredSelectMultiple(
                verbose_name="ДОСТУПНОЕ ОБОРУДОВАНИЕ",
                is_stacked=False
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """
        🔒 Ограничиваем должности по организациям, доступным пользователю.
        """
        qs = super().get_queryset(request).select_related(
            'organization',
            'subdivision',
            'department'
        ).prefetch_related(
            'documents',
            'equipment'
        )
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form для:
        1) Передачи request.user в форму
        2) Фильтрации M2M-полей по организациям
        """
        Form = super().get_form(request, obj, **kwargs)

        class PositionFormWithUser(Form):
            def __init__(self, *args, **kwargs):
                self.user = request.user
                super().__init__(*args, **kwargs)

                # Настраиваем labels и help_text для полей
                self.fields['documents'].label = "ДОСТУПНЫЕ ДОКУМЕНТЫ"
                self.fields['equipment'].label = "ДОСТУПНОЕ ОБОРУДОВАНИЕ"

                self.fields['documents'].help_text = "Удерживайте 'Control' (или 'Command' на Mac), чтобы выбрать несколько значений."
                self.fields['equipment'].help_text = "Удерживайте 'Control' (или 'Command' на Mac), чтобы выбрать несколько значений."

                # Фильтруем документы и оборудование по организациям
                if hasattr(request.user, 'profile'):
                    allowed_orgs = request.user.profile.organizations.all()

                    # Базовые queryset
                    docs_qs = self.fields['documents'].queryset
                    equip_qs = self.fields['equipment'].queryset

                    # Если редактируем существующий объект
                    if obj:
                        # Фильтруем по организации объекта
                        docs_qs = docs_qs.filter(organization=obj.organization)
                        equip_qs = equip_qs.filter(organization=obj.organization)

                    # Фильтруем по доступным организациям
                    docs_qs = docs_qs.filter(organization__in=allowed_orgs).distinct().order_by('name')
                    equip_qs = equip_qs.filter(organization__in=allowed_orgs).distinct().order_by('equipment_name')

                    self.fields['documents'].queryset = docs_qs
                    self.fields['equipment'].queryset = equip_qs

        return PositionFormWithUser

    def get_additional_node_data(self, obj):
        """
        ➕ Дополнительные данные для узла: роли и атрибуты должности.
        """
        return {
            'is_responsible_for_safety': obj.is_responsible_for_safety,
            'can_be_internship_leader': obj.can_be_internship_leader,
            'commission_role': obj.commission_role,
            'is_electrical_personnel': obj.is_electrical_personnel,
            'documents_count': obj.documents.count(),
            'equipment_count': obj.equipment.count(),
        }

    def has_module_permission(self, request):
        """
        👮‍♂️ Проверка прав на доступ к модулю
        """
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.organizations.exists()
        return False

    def has_view_permission(self, request, obj=None):
        """
        👀 Проверка прав на просмотр
        """
        if request.user.is_superuser:
            return True
        if not obj:
            return True
        if hasattr(request.user, 'profile'):
            return obj.organization in request.user.profile.organizations.all()
        return False

    def has_change_permission(self, request, obj=None):
        """
        ✏️ Проверка прав на редактирование
        """
        return self.has_view_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """
        🗑️ Проверка прав на удаление
        """
        return self.has_view_permission(request, obj)

    def has_add_permission(self, request):
        """
        ➕ Проверка прав на добавление
        """
        if request.user.is_superuser:
            return True
        if hasattr(request.user, 'profile'):
            return request.user.profile.organizations.exists()
        return False