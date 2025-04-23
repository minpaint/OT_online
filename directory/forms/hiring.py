# directory/forms/hiring.py
from django import forms
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Button, Row, Column
from dal import autocomplete

from directory.models import EmployeeHiring, Employee, GeneratedDocument
from directory.forms.mixins import OrganizationRestrictionFormMixin


class CombinedEmployeeHiringForm(OrganizationRestrictionFormMixin, forms.Form):
    """
    👥 Форма для одновременного создания сотрудника и записи о приеме на работу.
    """
    # Поля сотрудника (Employee)
    full_name_nominative = forms.CharField(
        label=_("ФИО (именительный)"),
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    date_of_birth = forms.DateField(
        label=_("Дата рождения"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    place_of_residence = forms.CharField(
        label=_("Место проживания"),
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )

    # Поля для записи о приеме (EmployeeHiring)
    hiring_date = forms.DateField(
        label=_("Дата приема"),
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    start_date = forms.DateField(
        label=_("Дата начала работы"),
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    hiring_type = forms.ChoiceField(
        label=_("Вид приема"),
        choices=EmployeeHiring.HIRING_TYPE_CHOICES,
        initial='new',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    contract_type = forms.ChoiceField(
        label=_("Тип договора"),
        choices=Employee.CONTRACT_TYPE_CHOICES,
        initial='standard',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Организационная структура
    organization = forms.ModelChoiceField(
        label=_("Организация"),
        queryset=None,  # Будет заполнено в __init__
        widget=autocomplete.ModelSelect2(
            url='directory:organization-autocomplete',
            attrs={
                'data-placeholder': '🏢 Выберите организацию...',
                'class': 'select2 form-control',
                'data-theme': 'bootstrap4'
            }
        )
    )
    subdivision = forms.ModelChoiceField(
        label=_("Подразделение"),
        queryset=None,  # Будет заполнено в __init__
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:subdivision-autocomplete',
            forward=['organization'],
            attrs={
                'data-placeholder': '🏭 Выберите подразделение...',
                'class': 'select2 form-control',
                'data-theme': 'bootstrap4'
            }
        )
    )
    department = forms.ModelChoiceField(
        label=_("Отдел"),
        queryset=None,  # Будет заполнено в __init__
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision'],
            attrs={
                'data-placeholder': '📂 Выберите отдел...',
                'class': 'select2 form-control',
                'data-theme': 'bootstrap4'
            }
        )
    )
    position = forms.ModelChoiceField(
        label=_("Должность"),
        queryset=None,  # Будет заполнено в __init__
        widget=autocomplete.ModelSelect2(
            url='directory:position-autocomplete',
            forward=['organization', 'subdivision', 'department'],
            attrs={
                'data-placeholder': '👔 Выберите должность...',
                'class': 'select2 form-control',
                'data-theme': 'bootstrap4'
            }
        )
    )

    # Размеры для спецодежды
    height = forms.ChoiceField(
        label=_("Рост"),
        choices=Employee.HEIGHT_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    clothing_size = forms.ChoiceField(
        label=_("Размер одежды"),
        choices=Employee.CLOTHING_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    shoe_size = forms.ChoiceField(
        label=_("Размер обуви"),
        choices=Employee.SHOE_SIZE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    # Дополнительные поля
    notes = forms.CharField(
        label=_("Примечания"),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                _('Информация о приеме на работу'),
                Row(
                    Column('hiring_date', css_class='col-md-6'),
                    Column('start_date', css_class='col-md-6'),
                ),
                Row(
                    Column('hiring_type', css_class='col-md-6'),
                    Column('contract_type', css_class='col-md-6'),
                ),
                css_class='mb-3'
            ),
            Fieldset(
                _('Организационная структура'),
                'organization',
                Row(
                    Column('subdivision', css_class='col-md-6'),
                    Column('department', css_class='col-md-6'),
                ),
                'position',
                css_class='mb-3'
            ),
            Fieldset(
                _('Информация о сотруднике'),
                'full_name_nominative',
                'date_of_birth',
                'place_of_residence',
                css_class='mb-3'
            ),
            Fieldset(
                _('Размеры для спецодежды'),
                Row(
                    Column('height', css_class='col-md-4'),
                    Column('clothing_size', css_class='col-md-4'),
                    Column('shoe_size', css_class='col-md-4'),
                ),
                css_class='mb-3'
            ),
            Fieldset(
                _('Дополнительно'),
                'notes',
                css_class='mb-3'
            ),
            Div(
                Submit('submit', '💾 Сохранить', css_class='btn-primary'),
                Button('preview', '👁️ Предпросмотр', css_class='btn-info', type='submit'),
                HTML('<a href="{% url "directory:hiring:hiring_list" %}" class="btn btn-secondary">Отмена</a>'),
                css_class='d-flex justify-content-between'
            )
        )

        # Заполнение queryset для полей с моделями
        from directory.models import Organization, StructuralSubdivision, Department, Position

        # Ограничение организаций по профилю пользователя
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs

            # Если у пользователя одна организация, выбираем ее по умолчанию
            if user_orgs.count() == 1:
                org = user_orgs.first()
                self.initial['organization'] = org.id
                self.fields['subdivision'].queryset = StructuralSubdivision.objects.filter(organization=org)
            else:
                self.fields['subdivision'].queryset = StructuralSubdivision.objects.none()
        else:
            self.fields['organization'].queryset = Organization.objects.all()
            self.fields['subdivision'].queryset = StructuralSubdivision.objects.none()

        # Пустые начальные queryset для зависимых полей
        self.fields['department'].queryset = Department.objects.none()
        self.fields['position'].queryset = Position.objects.all()

    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hiring_date')
        start_date = cleaned_data.get('start_date')

        if hire_date and start_date and start_date < hire_date:
            self.add_error('start_date', _("Дата начала работы не может быть раньше даты приема"))

        return cleaned_data

    @transaction.atomic
    def save(self, commit=True):
        """
        Одновременно создает сотрудника и запись о приеме.
        """
        # Создаем сотрудника
        from directory.utils.declension import decline_full_name

        employee = Employee(
            full_name_nominative=self.cleaned_data['full_name_nominative'],
            full_name_dative=decline_full_name(self.cleaned_data['full_name_nominative'], 'datv'),
            date_of_birth=self.cleaned_data['date_of_birth'],
            place_of_residence=self.cleaned_data['place_of_residence'],
            organization=self.cleaned_data['organization'],
            subdivision=self.cleaned_data.get('subdivision'),
            department=self.cleaned_data.get('department'),
            position=self.cleaned_data['position'],
            height=self.cleaned_data.get('height', ''),
            clothing_size=self.cleaned_data.get('clothing_size', ''),
            shoe_size=self.cleaned_data.get('shoe_size', ''),
            contract_type=self.cleaned_data['contract_type'],
            hire_date=self.cleaned_data['hiring_date'],
            start_date=self.cleaned_data['start_date'],
        )

        # Обновляем is_contractor на основе contract_type
        employee.is_contractor = (employee.contract_type == 'contractor')

        if commit:
            employee.save()

        # Создаем запись о приеме
        hiring = EmployeeHiring(
            employee=employee,
            hiring_date=self.cleaned_data['hiring_date'],
            start_date=self.cleaned_data['start_date'],
            hiring_type=self.cleaned_data['hiring_type'],
            organization=self.cleaned_data['organization'],
            subdivision=self.cleaned_data.get('subdivision'),
            department=self.cleaned_data.get('department'),
            position=self.cleaned_data['position'],
            notes=self.cleaned_data.get('notes', ''),
            created_by=self.user
        )

        if commit:
            hiring.save()

        return employee, hiring


class EmployeeHiringRecordForm(OrganizationRestrictionFormMixin, forms.ModelForm):
    """
    📝 Форма для создания и редактирования только записи о приеме на работу
    (без создания сотрудника)
    """

    class Meta:
        model = EmployeeHiring
        fields = [
            'employee', 'hiring_date', 'start_date', 'hiring_type',
            'organization', 'subdivision', 'department', 'position',
            'notes', 'is_active'
        ]
        widgets = {
            'hiring_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee': autocomplete.ModelSelect2(
                url='directory:employee-autocomplete',
                attrs={
                    'data-placeholder': '👤 Выберите сотрудника...',
                    'class': 'select2 form-control'
                }
            ),
            'organization': autocomplete.ModelSelect2(
                url='directory:organization-autocomplete',
                attrs={
                    'data-placeholder': '🏢 Выберите организацию...',
                    'class': 'select2 form-control'
                }
            ),
            'subdivision': autocomplete.ModelSelect2(
                url='directory:subdivision-autocomplete',
                forward=['organization'],
                attrs={
                    'data-placeholder': '🏭 Выберите подразделение...',
                    'class': 'select2 form-control'
                }
            ),
            'department': autocomplete.ModelSelect2(
                url='directory:department-autocomplete',
                forward=['subdivision'],
                attrs={
                    'data-placeholder': '📂 Выберите отдел...',
                    'class': 'select2 form-control'
                }
            ),
            'position': autocomplete.ModelSelect2(
                url='directory:position-autocomplete',
                forward=['organization', 'subdivision', 'department'],
                attrs={
                    'data-placeholder': '👔 Выберите должность...',
                    'class': 'select2 form-control'
                }
            ),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настройка crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Fieldset(
                _('Основная информация'),
                'employee',
                Row(
                    Column('hiring_date', css_class='col-md-6'),
                    Column('start_date', css_class='col-md-6'),
                ),
                'hiring_type',
                css_class='mb-3'
            ),
            Fieldset(
                _('Организационная структура'),
                'organization',
                Row(
                    Column('subdivision', css_class='col-md-6'),
                    Column('department', css_class='col-md-6'),
                ),
                'position',
                css_class='mb-3'
            ),
            Fieldset(
                _('Дополнительно'),
                'notes',
                'is_active',
                css_class='mb-3'
            ),
            Div(
                Submit('submit', '💾 Сохранить', css_class='btn-primary'),
                HTML('<a href="{% url "directory:hiring:hiring_list" %}" class="btn btn-secondary">Отмена</a>'),
                css_class='d-flex justify-content-between'
            )
        )


class DocumentAttachmentForm(forms.Form):
    """
    📎 Форма для прикрепления существующих документов к записи о приеме
    """
    documents = forms.ModelMultipleChoiceField(
        queryset=GeneratedDocument.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Выберите документы для прикрепления")
    )

    def __init__(self, *args, **kwargs):
        employee_id = kwargs.pop('employee_id', None)
        super().__init__(*args, **kwargs)

        # Фильтруем документы по сотруднику
        if employee_id:
            self.fields['documents'].queryset = GeneratedDocument.objects.filter(
                employee_id=employee_id
            ).order_by('-created_at')

            # Добавляем аннотацию типа документа для более понятного отображения
            self.fields['documents'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        """Форматирует метку для документа в списке"""
        if obj.template:
            type_name = obj.template.get_document_type_display()
            created_at = obj.created_at.strftime("%d.m.%Y %H:%M")
            return f"{type_name} ({created_at})"
        return f"Документ #{obj.id} ({obj.created_at.strftime('%d.m.%Y')})"