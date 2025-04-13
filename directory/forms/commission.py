from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Field, Row, Column
from dal import autocomplete
from directory.models import Commission, CommissionMember, Employee, Organization, StructuralSubdivision as Subdivision, \
    Department
from .mixins import OrganizationRestrictionFormMixin


class CommissionForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    """Форма для создания и редактирования комиссии с иерархическим выбором структуры"""

    class Meta:
        model = Commission
        fields = ['name', 'commission_type', 'organization', 'subdivision', 'department', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_type': forms.Select(attrs={'class': 'form-control'}),
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={'data-placeholder': '🏢 Выберите организацию...'}
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={'data-placeholder': '🏭 Выберите подразделение...'}
            ),
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={'data-placeholder': '📂 Выберите отдел...'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настройка внешнего вида формы
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Основная информация',
                'name',
                'commission_type',
                'is_active',
            ),
            Fieldset(
                'Привязка к структуре организации',
                HTML(
                    '<p class="text-info">Выберите только один уровень привязки: организация, подразделение или отдел</p>'),
                'organization',
                'subdivision',
                'department',
            ),
            ButtonHolder(
                Submit('submit', 'Сохранить', css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "directory:commissions:commission_list" %}" class="btn btn-secondary">Отмена</a>'),
            )
        )

        # Делаем поля необязательными для валидации на уровне формы
        self.fields['organization'].required = False
        self.fields['subdivision'].required = False
        self.fields['department'].required = False

        # Если пользователь привязан к организациям, ограничиваем выбор
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs

            if user_orgs.count() == 1:
                org = user_orgs.first()
                self.initial['organization'] = org.id
                self.fields['subdivision'].queryset = Subdivision.objects.filter(organization=org)
            else:
                self.fields['subdivision'].queryset = Subdivision.objects.none()

        # По умолчанию отделы недоступны пока не выбрано подразделение
        self.fields['department'].queryset = Department.objects.none()

        # Инициализация полей при редактировании
        if self.instance and self.instance.pk:
            if self.instance.organization:
                self.fields['subdivision'].queryset = Subdivision.objects.filter(
                    organization=self.instance.organization)
            if self.instance.subdivision:
                self.fields['department'].queryset = Department.objects.filter(subdivision=self.instance.subdivision)

    def clean(self):
        """Дополнительная валидация формы"""
        cleaned_data = super().clean()

        # Проверка, что выбран только один уровень привязки
        organization = cleaned_data.get('organization')
        subdivision = cleaned_data.get('subdivision')
        department = cleaned_data.get('department')

        bindings = sum(1 for field in [organization, subdivision, department] if field is not None)

        if bindings == 0:
            raise ValidationError('Необходимо выбрать организацию, структурное подразделение или отдел.')
        elif bindings > 1:
            raise ValidationError(
                'Комиссия должна быть привязана только к одному уровню: организация, '
                'структурное подразделение или отдел.'
            )

        return cleaned_data


class CommissionMemberForm(forms.ModelForm):
    """Форма для добавления и редактирования участника комиссии"""

    class Meta:
        model = CommissionMember
        fields = ['commission', 'employee', 'role', 'is_active']
        widgets = {
            'commission': forms.HiddenInput(),
            'employee': autocomplete.ModelSelect2(
                url='directory:employee-autocomplete',
                forward=['commission'],
                attrs={'data-placeholder': '👤 Выберите сотрудника...'}
            ),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        commission = kwargs.pop('commission', None)
        super().__init__(*args, **kwargs)

        # Настройка внешнего вида формы
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'commission',
            Row(
                Column('employee', css_class='form-group col-md-6'),
                Column('role', css_class='form-group col-md-6'),
                css_class='form-row'
            ),
            'is_active',
            ButtonHolder(
                Submit('submit', 'Сохранить', css_class='btn btn-primary'),
                HTML(
                    '<a href="{% url "directory:commissions:commission_detail" commission.id %}" class="btn btn-secondary">Отмена</a>'),
            )
        )

        # Устанавливаем комиссию в скрытое поле
        if commission:
            self.fields['commission'].initial = commission.id

        # Получаем занятые роли для визуализации в форме
        existing_roles = []
        if commission:
            existing_roles = list(commission.members.filter(
                is_active=True
            ).exclude(
                id=self.instance.id if self.instance and self.instance.id else None
            ).values_list('role', flat=True))

        # Создаем список ролей с информацией о том, какие уже заняты
        self.role_choices = []
        for value, label in self.fields['role'].choices:
            disabled = False
            tooltip = ""
            if value in ['chairman', 'secretary'] and value in existing_roles:
                disabled = True
                tooltip = f"Роль {label} уже занята"

            self.role_choices.append((value, label, disabled, tooltip))

    def clean(self):
        """Дополнительная валидация формы"""
        cleaned_data = super().clean()

        commission = cleaned_data.get('commission')
        role = cleaned_data.get('role')
        is_active = cleaned_data.get('is_active')

        # Проверка на дубликаты ролей председателя и секретаря
        if is_active and role in ['chairman', 'secretary']:
            existing = CommissionMember.objects.filter(
                commission=commission,
                role=role,
                is_active=True
            )

            # Если это редактирование, исключаем текущий экземпляр из проверки
            if self.instance and self.instance.pk:
                existing = existing.exclude(id=self.instance.id)

            if existing.exists():
                role_display = dict(CommissionMember.ROLE_CHOICES)[role]
                raise ValidationError(
                    f'В комиссии уже есть активный {role_display.lower()}. '
                    'Пожалуйста, деактивируйте его перед назначением нового.'
                )

        return cleaned_data