# directory/forms/commission.py

from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Field, Row, Column
from directory.models import Commission, CommissionMember, Employee


class CommissionForm(forms.ModelForm):
    """Форма для создания и редактирования комиссии"""

    class Meta:
        model = Commission
        fields = ['name', 'commission_type', 'organization', 'subdivision', 'department', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'commission_type': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'subdivision': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
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

    def clean(self):
        """Дополнительная валидация формы"""
        cleaned_data = super().clean()

        # Проверка, что выбран только один уровень привязки
        organization = cleaned_data.get('organization')
        subdivision = cleaned_data.get('subdivision')
        department = cleaned_data.get('department')

        bindings = sum(1 for field in [organization, subdivision, department] if field is not None)

        if bindings == 0:
            raise ValidationError(
                'Необходимо выбрать организацию, структурное подразделение или отдел.'
            )
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
            'employee': forms.Select(attrs={'class': 'form-control select2'}),
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

        # Если комиссия передана, ограничиваем выбор сотрудников только своей организацией
        if commission:
            if commission.department:
                # Сотрудники этого отдела
                employees = Employee.objects.filter(department=commission.department)
            elif commission.subdivision:
                # Сотрудники этого подразделения
                employees = Employee.objects.filter(subdivision=commission.subdivision)
            elif commission.organization:
                # Сотрудники этой организации
                employees = Employee.objects.filter(organization=commission.organization)
            else:
                employees = Employee.objects.none()

            self.fields['employee'].queryset = employees
            self.fields['commission'].initial = commission.id
        else:
            # Если комиссия не передана, но это редактирование существующего участника
            if self.instance and self.instance.pk:
                commission = self.instance.commission

                if commission.department:
                    employees = Employee.objects.filter(department=commission.department)
                elif commission.subdivision:
                    employees = Employee.objects.filter(subdivision=commission.subdivision)
                elif commission.organization:
                    employees = Employee.objects.filter(organization=commission.organization)
                else:
                    employees = Employee.objects.none()

                self.fields['employee'].queryset = employees

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