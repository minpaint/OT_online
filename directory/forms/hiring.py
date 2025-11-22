# directory/forms/hiring.py
from django import forms
from django.utils.translation import gettext_lazy as _
# from django.utils import timezone
# from django.db import transaction
# from django.forms import formset_factory

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Row, Column, Field
from dal import autocomplete

from directory.models import (
    Employee,
    EmployeeHiring,
    Organization,
    Position,
    StructuralSubdivision,
    Department,
    GeneratedDocument
)
from deadline_control.models.medical_norm import MedicalExaminationNorm


class CombinedEmployeeHiringForm(forms.Form):
    """
    👨‍💼 Форма для единовременного создания сотрудника и записи о приеме
    с изменением порядка полей (ФИО и Вид приема первыми)
    и поддержкой дополнительных полей для медосмотра и СИЗ.
    """
    full_name_nominative = forms.CharField(
        label=_("ФИО (именительный падеж)"),
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Иванов Иван Иванович'
        })
    )

    hiring_type = forms.ChoiceField(
        label=_("Вид приема"),
        choices=EmployeeHiring.HIRING_TYPE_CHOICES,
        initial='new',
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Организация*"),
        required=True,
        widget=autocomplete.ModelSelect2(
            url='directory:organization-autocomplete',
            attrs={
                'data-placeholder': '🏢 Выберите организацию...',
                'class': 'select2 form-control'
            }
        )
    )

    subdivision = forms.ModelChoiceField(
        queryset=StructuralSubdivision.objects.none(),
        label=_("Структурное подразделение"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:subdivision-autocomplete',
            forward=['organization'],
            attrs={
                'data-placeholder': '🏭 Выберите подразделение...',
                'class': 'select2 form-control'
            }
        )
    )

    department = forms.ModelChoiceField(
        queryset=Department.objects.none(),
        label=_("Отдел"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision', 'organization'],
            attrs={
                'data-placeholder': '📂 Выберите отдел...',
                'class': 'select2 form-control'
            }
        )
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        label=_("Должность*"),
        required=True,
        widget=autocomplete.ModelSelect2(
            url='directory:position-autocomplete',
            forward=['organization', 'subdivision', 'department'],
            attrs={
                'data-placeholder': '👔 Выберите должность...',
                'class': 'select2 form-control'
            }
        )
    )

    date_of_birth = forms.DateField(
        label=_("Дата рождения"),
        required=True,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            },
            format='%Y-%m-%d'
        )
    )

    initial_medical_examination_date = forms.DateField(
        label=_("Дата первичного медосмотра"),
        required=False,
        help_text=_("Работник должен быть до начала работы направлен на медицинский осмотр. "
                    "Если по результатам медицинского осмотра он годен, то укажите дату медосмотра."),
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            },
            format='%Y-%m-%d'
        )
    )

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

    contract_type = forms.ChoiceField(
        label=_("Тип договора"),
        choices=Employee.CONTRACT_TYPE_CHOICES,
        initial='standard',
        required=False,
        widget=forms.HiddenInput()
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'hiring-form'
        self.helper.attrs = {'novalidate': ''}  # Отключаем HTML5 валидацию для Select2

        self.helper.layout = Layout(
            # Персональные данные - компактно в одну строку
            Fieldset(
                '',  # Убираем заголовок - он будет в карточке
                HTML('<h5 class="section-title mb-3"><i class="fas fa-user"></i> Персональные данные</h5>'),
                Row(
                    Column('full_name_nominative', css_class='form-group col-md-5 mb-3'),
                    Column('date_of_birth', css_class='form-group col-md-3 mb-3'),
                    Column('hiring_type', css_class='form-group col-md-4 mb-3'),
                ),
                css_class='form-section'
            ),

            # Организационная структура - компактнее, в 2 колонки
            Fieldset(
                '',
                HTML('<h5 class="section-title mb-3 mt-4"><i class="fas fa-sitemap"></i> Организационная структура</h5>'),
                Row(
                    Column('organization', css_class='form-group col-md-6 mb-3'),
                    Column('subdivision', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('department', css_class='form-group col-md-6 mb-3'),
                    Column('position', css_class='form-group col-md-6 mb-3'),
                ),
                css_class='form-section'
            ),

            # Медосмотр - скрытая секция
            Div(
                HTML('<h5 class="section-title mb-3 mt-4"><i class="fas fa-stethoscope"></i> Информация для медосмотра</h5>'),
                HTML('<div class="alert alert-info mb-3"><i class="fas fa-info-circle"></i> Для данной должности требуется медицинский осмотр. Пожалуйста, заполните необходимые данные.</div>'),
                Row(
                    Column('initial_medical_examination_date', css_class='form-group col-md-6 mb-3'),
                ),
                css_class='form-section d-none',
                id='medical-section'
            ),

            # СИЗ - скрытая секция
            Div(
                HTML('<h5 class="section-title mb-3 mt-4"><i class="fas fa-hard-hat"></i> Информация для СИЗ</h5>'),
                HTML('<div class="alert alert-success mb-3"><i class="fas fa-info-circle"></i> Для данной должности предусмотрена выдача СИЗ. Укажите антропометрические данные.</div>'),
                Row(
                    Column('height', css_class='form-group col-md-4 mb-3'),
                    Column('clothing_size', css_class='form-group col-md-4 mb-3'),
                    Column('shoe_size', css_class='form-group col-md-4 mb-3'),
                ),
                css_class='form-section d-none',
                id='siz-section'
            ),

            'contract_type',

            # Кнопки управления
            Div(
                HTML('<hr class="my-4">'),
                Div(
                    HTML('<a href="/directory/hiring/list/" class="btn btn-outline-secondary btn-lg mr-3"><i class="fas fa-times"></i> Отмена</a>'),
                    Submit('submit', '✓ Принять на работу', css_class='btn btn-success btn-lg'),
                    css_class='d-flex justify-content-between align-items-center'
                ),
                css_class='form-actions mt-4'
            )
        )

        if self.user and hasattr(self.user, 'profile') and not self.user.is_superuser:
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
            if user_orgs.count() == 1 and not self.data.get('organization') and not self.initial.get('organization'):
                self.initial['organization'] = user_orgs.first().pk
        else:
            self.fields['organization'].queryset = Organization.objects.all()

        organization_value = None
        if self.is_bound:
            organization_value = self.data.get('organization')
        elif self.initial:
            organization_value = self.initial.get('organization')

        organization_pk = None
        if organization_value:
            if isinstance(organization_value, Organization):
                organization_pk = organization_value.pk
            else:
                try:
                    organization_pk = int(organization_value)
                except (ValueError, TypeError):
                    organization_pk = None

        if organization_pk:
            org_q = Organization.objects.filter(pk=organization_pk)
            if not org_q.exists():
                organization_pk = None

        base_subdivision_qs = StructuralSubdivision.objects.all()
        base_department_qs = Department.objects.all()
        base_position_qs = Position.objects.all()

        if organization_pk:
            self.fields['subdivision'].queryset = base_subdivision_qs.filter(organization_id=organization_pk)
            self.fields['department'].queryset = base_department_qs.filter(organization_id=organization_pk)
            self.fields['position'].queryset = base_position_qs.filter(organization_id=organization_pk)

            subdivision_value = None
            if self.is_bound:
                subdivision_value = self.data.get('subdivision')
            elif self.initial:
                subdivision_value = self.initial.get('subdivision')

            subdivision_pk = None
            if subdivision_value:
                if isinstance(subdivision_value, StructuralSubdivision):
                    subdivision_pk = subdivision_value.pk
                else:
                    try:
                        subdivision_pk = int(subdivision_value)
                    except(ValueError, TypeError):
                        subdivision_pk = None

            if subdivision_pk:
                sub_q = self.fields['subdivision'].queryset.filter(pk=subdivision_pk)
                if not sub_q.exists():
                    subdivision_pk = None

            if subdivision_pk:
                self.fields['department'].queryset = base_department_qs.filter(
                    subdivision_id=subdivision_pk,
                    organization_id=organization_pk
                )
                self.fields['position'].queryset = base_position_qs.filter(
                    subdivision_id=subdivision_pk,
                    organization_id=organization_pk
                )

                department_value = None
                if self.is_bound:
                    department_value = self.data.get('department')
                elif self.initial:
                    department_value = self.initial.get('department')

                department_pk = None
                if department_value:
                    if isinstance(department_value, Department):
                        department_pk = department_value.pk
                    else:
                        try:
                            department_pk = int(department_value)
                        except(ValueError, TypeError):
                            department_pk = None

                if department_pk:
                    dept_q = self.fields['department'].queryset.filter(pk=department_pk)
                    if not dept_q.exists():
                        department_pk = None

                if department_pk:
                    self.fields['position'].queryset = base_position_qs.filter(
                        department_id=department_pk,
                        subdivision_id=subdivision_pk,
                        organization_id=organization_pk
                    )
            else:
                self.fields['department'].queryset = base_department_qs.filter(
                    organization_id=organization_pk,
                    subdivision__isnull=True
                )
                self.fields['position'].queryset = base_position_qs.filter(
                    organization_id=organization_pk,
                    subdivision__isnull=True,
                    department__isnull=True
                )
        else:
            self.fields['subdivision'].queryset = StructuralSubdivision.objects.none()
            self.fields['department'].queryset = Department.objects.none()
            self.fields[
                'position'].queryset = Position.objects.all()  # Оставляем .all() если организация не выбрана, как было в определении поля

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')

        if position:
            needs_medical = False
            if hasattr(position, 'medical_factors') and hasattr(position.medical_factors, 'filter'):
                needs_medical = position.medical_factors.filter(is_disabled=False).exists()

            if not needs_medical:
                needs_medical = MedicalExaminationNorm.objects.filter(
                    position_name=position.position_name
                ).exists()

            if needs_medical:
                date_of_birth = cleaned_data.get('date_of_birth')

                if not date_of_birth:
                    self.add_error('date_of_birth', _('Необходимо указать дату рождения для медосмотра.'))

            needs_siz = False
            if hasattr(position, 'siz_norms') and hasattr(position.siz_norms, 'exists'):
                needs_siz = position.siz_norms.exists()

            if not needs_siz:
                if hasattr(Position, 'find_reference_norms'):
                    needs_siz = Position.find_reference_norms(position.position_name).exists()
        return cleaned_data


class DocumentAttachmentForm(forms.Form):
    documents = forms.ModelMultipleChoiceField(
        queryset=GeneratedDocument.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_("Выберите документы для прикрепления")
    )

    def __init__(self, *args, **kwargs):
        employee_id = kwargs.pop('employee_id', None)
        super().__init__(*args, **kwargs)

        if employee_id:
            self.fields['documents'].queryset = GeneratedDocument.objects.filter(
                employee_id=employee_id
            ).order_by('-created_at')
            self.fields['documents'].label_from_instance = self.label_from_instance_custom

    @staticmethod
    def label_from_instance_custom(obj):
        if hasattr(obj, 'template') and obj.template and hasattr(obj.template, 'get_document_type_display'):
            type_name = obj.template.get_document_type_display()
            created_at_str = obj.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(obj,
                                                                                  'created_at') and obj.created_at else "N/A"
            return f"{type_name} ({created_at_str})"
        created_at_str_default = obj.created_at.strftime('%d.%m.%Y') if hasattr(obj,
                                                                                'created_at') and obj.created_at else "N/A"
        return f"Документ #{obj.id} ({created_at_str_default})"