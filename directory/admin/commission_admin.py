from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from directory.models import Commission, CommissionMember, Employee


class CommissionMemberInline(admin.TabularInline):
    """Встроенная админка для участников комиссии"""
    model = CommissionMember
    extra = 1
    fields = ['employee', 'role', 'is_active']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # ИСПРАВЛЕНИЕ: Переопределяем виджет для поля employee
        if db_field.name == 'employee':
            # Получаем объект комиссии, если он есть в request
            obj = getattr(request, '_obj_', None)
            forward = []

            # Если комиссия существует и сохранена, добавляем forward параметры
            if obj and obj.pk:
                forward = [
                    ('commission', obj.pk),
                    ('organization', obj.organization_id or ''),
                    ('subdivision', obj.subdivision_id or ''),
                    ('department', obj.department_id or '')
                ]

            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:employee-for-commission-autocomplete',
                forward=forward,
                attrs={'data-placeholder': 'Выберите сотрудника...'}
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        # ИСПРАВЛЕНИЕ: Передаем информацию о комиссии в inline-форму только если она сохранена
        formset = super().get_formset(request, obj, **kwargs)

        # Устанавливаем параметры forward только если комиссия сохранена
        if obj and obj.pk:  # Только если объект комиссии уже сохранен
            if 'employee' in formset.form.base_fields:
                formset.form.base_fields['employee'].widget.forward = [
                    ('commission', obj.pk),
                    ('organization', obj.organization_id or ''),
                    ('subdivision', obj.subdivision_id or ''),
                    ('department', obj.department_id or '')
                ]
        else:
            # Для новой комиссии временно отключаем forward параметры
            if 'employee' in formset.form.base_fields:
                formset.form.base_fields['employee'].widget.forward = []

        return formset


@admin.register(Commission)
class CommissionAdmin(admin.ModelAdmin):
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

    # ИСПРАВЛЕНИЕ: Сохраняем объект в request для использования в inline формах
    def get_form(self, request, obj=None, **kwargs):
        # Сохраняем объект в request, чтобы использовать в inline формах
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

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
        )


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