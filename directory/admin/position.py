# directory/admin/position.py

from django.contrib import admin
from django.db.models import Q
from directory.models import Position
from directory.forms import PositionForm


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    👔 Админ-класс для модели Position.
    """
    form = PositionForm

    # Теперь выводим только нужные поля:
    list_display = [
        'position_name',   # Название должности
        'organization',    # Организация
        'subdivision',     # Подразделение
        'department',      # Отдел
    ]

    # Уберём из фильтра ненужные поля; оставим только базовые:
    list_filter = [
        'organization',
        'subdivision',
        'department',
    ]

    # Поиск оставим по названию и номерам инструкций (при желании можно убрать)
    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]

    # Связанные документы и оборудование по-прежнему редактируем через filter_horizontal
    filter_horizontal = ['documents', 'equipment']

    # Сохраняем текущую структуру fieldsets, чтобы поля оставались доступны в форме
    fieldsets = (
        (None, {
            'fields': ('position_name', 'commission_role')
        }),
        ('Организационная структура', {
            'fields': ('organization', 'subdivision', 'department')
        }),
        ('Безопасность', {
            'fields': (
                'safety_instructions_numbers',
                'electrical_safety_group',
                'internship_period_days',
                'is_responsible_for_safety',
                'is_electrical_personnel',
                'can_be_internship_leader'
            ),
            'description': '🔒 Настройки безопасности и допусков'
        }),
        ('📋 Договор подряда', {
            'fields': (
                'contract_work_name',
                'contract_safety_instructions'
            ),
            'description': '📝 Информация о работах по договору подряда',
            'classes': ('collapse',)
        }),
        ('Связанные документы и оборудование', {
            'fields': ('documents', 'equipment'),
            'description': '📄 Выберите документы и оборудование, относящиеся к данной должности',
            'classes': ('collapse',)
        }),
    )

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form, чтобы:
         1) Передать request.user в форму (для миксина).
         2) При редактировании фильтровать M2M-поля (documents и equipment) по организации объекта
            и по организациям, доступным пользователю.
        """
        OriginalForm = super().get_form(request, obj, **kwargs)

        class PositionFormWithUser(OriginalForm):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

                if hasattr(request.user, 'profile'):
                    allowed_orgs = request.user.profile.organizations.all()

                    # Базовые queryset для документов и оборудования
                    docs_qs = self2.fields['documents'].queryset
                    equip_qs = self2.fields['equipment'].queryset

                    # Если редактируем существующий объект, фильтруем по организации объекта
                    if obj:
                        docs_qs = docs_qs.filter(organization=obj.organization)
                        equip_qs = equip_qs.filter(organization=obj.organization)

                    # Фильтруем по разрешённым организациям пользователя
                    docs_qs = docs_qs.filter(organization__in=allowed_orgs).order_by('name')
                    equip_qs = equip_qs.filter(organization__in=allowed_orgs).order_by('equipment_name')

                    self2.fields['documents'].queryset = docs_qs
                    self2.fields['equipment'].queryset = equip_qs

        return PositionFormWithUser

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Настройка виджетов many-to-many с FilteredSelectMultiple."""
        if db_field.name == "documents":
            kwargs["widget"] = admin.widgets.FilteredSelectMultiple(
                "документы",
                is_stacked=False
            )
        if db_field.name == "equipment":
            kwargs["widget"] = admin.widgets.FilteredSelectMultiple(
                "оборудование",
                is_stacked=False
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_queryset(self, request):
        """
        🔒 Ограничиваем должности по организациям, доступным пользователю (если не суперпользователь).
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs

    class Media:
        css = {
            'all': [
                'admin/css/widgets.css',
            ]
        }
        js = [
            'admin/js/jquery.init.js',
            'admin/js/SelectFilter2.js',
        ]
