from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from django.core.exceptions import ValidationError
from directory.models import Commission, CommissionMember, Employee
from directory.admin.mixins.commission_tree_view import CommissionTreeViewMixin


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


@admin.register(Commission)
class CommissionAdmin(CommissionTreeViewMixin, admin.ModelAdmin):
    """Административный интерфейс для комиссий"""
    list_display = ['name', 'commission_type_display', 'level_display', 'members_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['name']
    inlines = [CommissionMemberInline]

    # Теперь комиссия может быть на любом из трёх уровней:
    # организация / подразделение / отдел
    # (при этом организация обязательна всегда)
    fieldsets = [
        (None, {
            'fields': ['name', 'commission_type', 'is_active']
        }),
        ('Привязка к структуре', {
            'fields': ['organization', 'subdivision', 'department'],
            'description': (
                "Заполните поля для выбора организации / подразделения / отдела. "
                "Если комиссия на уровне подразделения, укажите 'organization' и 'subdivision'. "
                "Если на уровне отдела, дополнительно заполните 'department'."
            )
        }),
    ]

    # Указываем, что поля должны использовать автодополнение
    autocomplete_fields = ['organization']

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Настраиваем иерархические зависимости (ModelSelect2):
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
        (комиссия -> участники комиссии).
        """
        instances = formset.save(commit=False)

        # Сначала сохраняем саму комиссию
        parent_obj = form.instance
        parent_obj.save()

        # Сохраняем связанные объекты (участников)
        for instance in instances:
            instance.commission = parent_obj
            instance.save()

        # Удаляем помеченные на удаление
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
        """Отображает текстовое описание уровня комиссии"""
        return obj.get_level_display()
    level_display.short_description = 'Уровень'

    def members_count(self, obj):
        """Отображает количество активных участников комиссии"""
        return obj.members.filter(is_active=True).count()
    members_count.short_description = 'Участников'

    class Media:
        js = (
            'directory/js/main.js',  # или ваш скрипт для дерева (если нужен здесь)
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

    def get_model_perms(self, request):
        """
        Скрывает модель из списка в админке, но сохраняет доступ по URL
        """
        return {}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Настраиваем автодополнение
        if db_field.name == 'commission':
            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:commission-autocomplete',
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
        # Дополнительная логика для подсказок по занятым ролям
        form = super().get_form(request, obj, **kwargs)

        if obj and obj.commission:
            existing_roles = list(
                obj.commission.members.filter(is_active=True)
                .exclude(id=obj.id if obj.id else None)
                .values_list('role', flat=True)
            )

            form.role_choices = []
            for value, label in form.base_fields['role'].choices:
                disabled = False
                tooltip = ""
                # Если 'chairman' или 'secretary' уже заняты, блокируем выбор
                if value in ['chairman', 'secretary'] and value in existing_roles:
                    disabled = True
                    tooltip = f"Роль {label} уже занята."
                form.role_choices.append((value, label, disabled, tooltip))
        return form

    def clean_form(self, request, obj=None):
        """
        Дополнительная валидация формы инлайна.
        На самом деле основная проверка в .clean() модели CommissionMember.
        """
        return super().clean_form(request, obj)
