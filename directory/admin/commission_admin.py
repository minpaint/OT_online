# directory/admin/commission_admin.py

from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from django.core.exceptions import ValidationError
from directory.models import Commission, CommissionMember, Employee
from directory.admin.mixins.tree_view import TreeViewMixin


class CommissionMemberInline(admin.TabularInline):
    """Встроенная админка для участников комиссии"""
    model = CommissionMember
    extra = 1
    fields = ['employee', 'role', 'is_active']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Переопределяем виджет для поля employee
        if db_field.name == 'employee':
            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:employee-for-commission-autocomplete',
                forward=['commission', 'organization', 'subdivision', 'department']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        # Передаем информацию о комиссии в inline-форму
        formset = super().get_formset(request, obj, **kwargs)
        if obj:  # Только если объект комиссии уже сохранен
            formset.form.base_fields['employee'].widget.forward = [
                ('commission', obj.pk),
                ('organization', obj.organization_id or ''),
                ('subdivision', obj.subdivision_id or ''),
                ('department', obj.department_id or '')
            ]
        return formset


class CommissionTreeViewMixin(TreeViewMixin):
    """
    Миксин для отображения комиссий в виде дерева с участниками.
    """
    change_list_template = "admin/directory/commission/change_list_tree.html"

    # Переопределяем настройки дерева для комиссий
    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'item': '🛡️',  # Иконка для комиссий по умолчанию
            'ot': '🛡️',  # Иконки для разных типов комиссий
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        },
        'fields': {
            'name_field': 'name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    def get_tree_data(self, request):
        """
        Переопределяем метод формирования дерева, чтобы включить информацию
        об участниках комиссии.
        """
        # Получаем базовое дерево из родительского метода
        tree = super().get_tree_data(request)

        # Обогащаем структуру дерева информацией об участниках комиссий
        self._enrich_tree_with_members(tree)

        return tree

    def _enrich_tree_with_members(self, tree):
        """
        Дополняет дерево информацией о составе комиссий.
        """
        # Проходим по всем организациям в дереве
        for org_data in tree.values():
            # Обрабатываем комиссии на уровне организации
            for item in org_data['items']:
                self._add_members_to_item(item)

            # Проходим по подразделениям
            for sub_data in org_data['subdivisions'].values():
                # Обрабатываем комиссии на уровне подразделения
                for item in sub_data['items']:
                    self._add_members_to_item(item)

                # Проходим по отделам
                for dept_data in sub_data['departments'].values():
                    # Обрабатываем комиссии на уровне отдела
                    for item in dept_data['items']:
                        self._add_members_to_item(item)

    def _add_members_to_item(self, item):
        """
        Добавляет информацию об участниках к комиссии.
        """
        obj = item['object']
        # Проверяем, что объект является комиссией
        if hasattr(obj, 'members'):
            # Получаем активных участников комиссии с prefetch_related
            members = obj.members.filter(is_active=True).select_related('employee')

            # Группируем участников по ролям
            roles = {
                'chairman': [],
                'secretary': [],
                'member': []
            }

            for member in members:
                roles[member.role].append({
                    'name': getattr(member.employee, 'full_name_nominative', str(member.employee)),
                    'position': getattr(member.employee, 'position_name', ''),
                    'role': member.get_role_display(),
                    'role_code': member.role
                })

            # Добавляем информацию об участниках в элемент дерева
            item['members'] = {
                'chairman': roles['chairman'],
                'secretary': roles['secretary'],
                'members': roles['member'],
                'total': len(members)
            }

            # Добавляем тип комиссии и статус активности
            item['commission_type'] = obj.commission_type
            item['is_active'] = obj.is_active

    def _optimize_queryset(self, queryset):
        """
        Оптимизируем запросы, добавляя prefetch_related для участников.
        """
        qs = super()._optimize_queryset(queryset)
        return qs.prefetch_related('members', 'members__employee')


@admin.register(Commission)
class CommissionAdmin(CommissionTreeViewMixin, admin.ModelAdmin):
    """Административный интерфейс для комиссий"""
    list_display = ['name', 'commission_type_display', 'level_display', 'members_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['name']
    inlines = [CommissionMemberInline]

    fieldsets = [
        (None, {'fields': ['name', 'commission_type', 'is_active']}),
        ('Привязка к структуре', {'fields': ['organization', 'subdivision', 'department']}),
    ]

    # Указываем, что поля должны использовать автодополнение
    autocomplete_fields = ['organization']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Настраиваем иерархические зависимости
        form.base_fields['subdivision'].widget = autocomplete.ModelSelect2(
            url='directory:subdivision-autocomplete',
            forward=['organization']
        )

        form.base_fields['department'].widget = autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision']
        )

        return form

    def save_formset(self, request, form, formset, change):
        """
        Переопределяем метод для обработки сохранения связанных объектов
        """
        instances = formset.save(commit=False)

        # Сначала сохраняем основной объект комиссии
        parent_obj = form.instance
        parent_obj.save()

        # Затем сохраняем связанные объекты
        for instance in instances:
            instance.commission = parent_obj  # Устанавливаем связь
            instance.save()

        # Обрабатываем удаление элементов, если есть
        for obj in formset.deleted_objects:
            obj.delete()

        formset.save_m2m()

    def commission_type_display(self, obj):
        """Отображает тип комиссии с иконкой"""
        icons = {
            'ot': '🛡️',
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        }
        icon = icons.get(obj.commission_type, '📋')
        return format_html('{} {}', icon, obj.get_commission_type_display())

    commission_type_display.short_description = 'Тип комиссии'

    def level_display(self, obj):
        """Отображает уровень комиссии"""
        return obj.get_level_display()

    level_display.short_description = 'Уровень'

    def members_count(self, obj):
        """Отображает количество активных участников комиссии"""
        count = obj.members.filter(is_active=True).count()
        return count

    members_count.short_description = 'Участников'

    class Media:
        js = (
            'admin/js/commission_admin.js',  # JavaScript для работы с зависимыми полями
            'admin/js/tree_view.js',  # JavaScript для работы с древовидным представлением
        )
        css = {
            'all': ('admin/css/tree_view.css',)
        }


@admin.register(CommissionMember)
class CommissionMemberAdmin(admin.ModelAdmin):
    """Административный интерфейс для участников комиссии"""
    list_display = ['employee', 'role_display', 'commission', 'is_active']
    list_filter = ['is_active', 'role', 'commission']
    search_fields = ['employee__full_name_nominative', 'commission__name']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Настраиваем автодополнение для полей
        if db_field.name == 'commission':
            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:commission-autocomplete',  # URL для автодополнения комиссий
                attrs={'data-placeholder': 'Выберите комиссию...'}
            )
        elif db_field.name == 'employee':
            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:employee-for-commission-autocomplete',
                forward=['commission'],
                attrs={'data-placeholder': 'Выберите сотрудника...'}
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def role_display(self, obj):
        """Отображает роль участника с иконкой"""
        icons = {
            'chairman': '👑',
            'member': '👤',
            'secretary': '📝'
        }
        icon = icons.get(obj.role, '👤')
        return format_html('{} {}', icon, obj.get_role_display())

    role_display.short_description = 'Роль'

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.commission:
            # Получаем занятые роли для визуализации
            existing_roles = list(obj.commission.members.filter(
                is_active=True
            ).exclude(
                id=obj.id if obj and obj.id else None
            ).values_list('role', flat=True))

            # Создаем дополнительное свойство для формы
            form.role_choices = []
            for value, label in form.base_fields['role'].choices:
                disabled = False
                tooltip = ""
                if value in ['chairman', 'secretary'] and value in existing_roles:
                    disabled = True
                    tooltip = f"Роль {label} уже занята"
                form.role_choices.append((value, label, disabled, tooltip))

        return form

    def clean_form(self, request, obj=None):
        """Дополнительная валидация формы"""
        form = super().clean_form(request, obj)

        if obj and obj.is_active and obj.role in ['chairman', 'secretary']:
            # Проверка на дубликаты ролей председателя и секретаря
            existing = CommissionMember.objects.filter(
                commission=obj.commission,
                role=obj.role,
                is_active=True
            )

            # Исключаем текущий экземпляр из проверки
            if obj.pk:
                existing = existing.exclude(id=obj.pk)

            if existing.exists():
                role_display = dict(CommissionMember.ROLE_CHOICES)[obj.role]
                self.message_user(
                    request,
                    f'В комиссии уже есть активный {role_display.lower()}. '
                    'Пожалуйста, деактивируйте его перед назначением нового.',
                    level='ERROR'
                )

        return form