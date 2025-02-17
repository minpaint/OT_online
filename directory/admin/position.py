from django.contrib import admin
from django.db.models import Q
from directory.models import Position
from directory.forms import PositionForm

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """
    👔 Админ-класс для модели Position
    """
    form = PositionForm

    list_display = [
        'position_name',
        'organization',
        'subdivision',
        'department',
        'get_commission_role_display',
        'electrical_safety_group',
        'can_be_internship_leader',
        'get_documents_count'
    ]

    list_filter = [
        'organization',
        'subdivision',
        'department',
        'commission_role',
        'electrical_safety_group',
        'can_be_internship_leader',
        'is_responsible_for_safety',
        'is_electrical_personnel'
    ]

    search_fields = [
        'position_name',
        'safety_instructions_numbers'
    ]

    filter_horizontal = ['documents', 'equipment']

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

    def get_commission_role_display(self, obj):
        """Отображение роли в комиссии с иконкой"""
        role_icons = {
            'chairman': '👑',
            'member': '👤',
            'secretary': '📝',
            'none': '❌'
        }
        return f"{role_icons.get(obj.commission_role, '')} {obj.get_commission_role_display()}"
    get_commission_role_display.short_description = "Роль в комиссии"
    get_commission_role_display.admin_order_field = 'commission_role'

    def get_documents_count(self, obj):
        """Отображение количества прикреплённых документов"""
        count = obj.documents.count()
        return f"📄 {count} док." if count > 0 else "Нет документов"
    get_documents_count.short_description = "Документы"

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form, чтобы:
        1) Передать request.user в форму (для OrganizationRestrictionFormMixin).
        2) Фильтровать ManyToMany-поля (документы, оборудование)
           при редактировании и при создании объекта.
        """
        original_form = super().get_form(request, obj, **kwargs)

        class PositionFormWithUser(original_form):
            def __init__(self2, *args, **inner_kwargs):
                # Передаём пользователя в форму (для миксина)
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

                # Базовый queryset для документов и оборудования
                base_docs_qs = self2.fields['documents'].queryset
                base_equip_qs = self2.fields['equipment'].queryset

                # 🏢 Фильтруем по профилю пользователя (если не суперпользователь)
                if not request.user.is_superuser and hasattr(request.user, 'profile'):
                    allowed_orgs = request.user.profile.organizations.all()
                    base_docs_qs = base_docs_qs.filter(organization__in=allowed_orgs)
                    base_equip_qs = base_equip_qs.filter(organization__in=allowed_orgs)

                if obj:
                    # Если редактируем существующий объект,
                    # дополнительно учитываем организацию/подразделение/отдел самой должности
                    base_docs_qs = base_docs_qs.filter(
                        Q(organization=obj.organization) &
                        (
                            Q(subdivision__isnull=True) |
                            Q(subdivision=obj.subdivision) |
                            (Q(department__isnull=True) | Q(department=obj.department))
                        )
                    ).order_by('name')

                    base_equip_qs = base_equip_qs.filter(
                        Q(organization=obj.organization) &
                        (
                            Q(subdivision__isnull=True) |
                            Q(subdivision=obj.subdivision) |
                            (Q(department__isnull=True) | Q(department=obj.department))
                        )
                    ).order_by('equipment_name')
                else:
                    # Если создаём новый объект (obj=None),
                    # мы пока не знаем, какую организацию выберут.
                    # Но всё равно отфильтруем хотя бы по allowed_orgs.
                    base_docs_qs = base_docs_qs.order_by('name')
                    base_equip_qs = base_equip_qs.order_by('equipment_name')

                # Устанавливаем итоговый queryset
                self2.fields['documents'].queryset = base_docs_qs
                self2.fields['equipment'].queryset = base_equip_qs

        return PositionFormWithUser

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """
        Настройка полей many-to-many с FilteredSelectMultiple.
        """
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
