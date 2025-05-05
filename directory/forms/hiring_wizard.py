from django import forms
from django.utils.translation import gettext_lazy as _
from dal import autocomplete
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Div, Submit, HTML, Row, Column, Field

from directory.models import (
    Employee,
    EmployeeHiring,
    Organization,
    Position,
    StructuralSubdivision,
    Department
)


class CombinedEmployeeHiringForm(forms.Form):
    """
    👨‍💼 Форма для единовременного создания сотрудника и записи о приеме
    с изменением порядка полей (ФИО и Вид приема первыми)
    и поддержкой дополнительных полей для медосмотра и СИЗ.
    """
    # Персональные данные (теперь первыми идут ФИО и Вид приема)
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

    # Организационная структура
    organization = forms.ModelChoiceField(
        queryset=Organization.objects.all(),
        label=_("Организация"),
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
            forward=['subdivision'],
            attrs={
                'data-placeholder': '📂 Выберите отдел...',
                'class': 'select2 form-control'
            }
        )
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        label=_("Должность"),
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

    # Данные для медосмотра (изначально скрыты, показываются по требованию должности)
    date_of_birth = forms.DateField(
        label=_("Дата рождения"),
        required=False,
        widget=forms.DateInput(
            attrs={
                'type': 'date',
                'class': 'form-control'
            },
            format='%Y-%m-%d'
        )
    )

    place_of_residence = forms.CharField(
        label=_("Место проживания"),
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Полный адрес места жительства'
            }
        )
    )

    # Данные для СИЗ (изначально скрыты, показываются по требованию должности)
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

    # Тип договора (скрытый по умолчанию)
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

        # Настройка crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'hiring-form'

        # Изменяем layout для отображения полей в нужном порядке
        self.helper.layout = Layout(
            # Секция персональных данных
            Fieldset(
                _('Персональные данные'),
                Row(
                    Column('full_name_nominative', css_class='col-md-8'),
                    Column('hiring_type', css_class='col-md-4'),
                ),
                css_class='form-section'
            ),

            # Секция организационной структуры
            Fieldset(
                _('Организационная структура'),
                'organization',
                Row(
                    Column('subdivision', css_class='col-md-6'),
                    Column('department', css_class='col-md-6'),
                ),
                'position',
                css_class='form-section'
            ),

            # Секция информации для медосмотра (будет показана при необходимости)
            Div(
                Fieldset(
                    _('Информация для медосмотра'),
                    Row(
                        Column('date_of_birth', css_class='col-md-6'),
                        Column('place_of_residence', css_class='col-md-6'),
                    ),
                ),
                css_class='form-section d-none',
                id='medical-section'
            ),

            # Секция информации для СИЗ (будет показана при необходимости)
            Div(
                Fieldset(
                    _('Информация для СИЗ'),
                    Row(
                        Column('height', css_class='col-md-4'),
                        Column('clothing_size', css_class='col-md-4'),
                        Column('shoe_size', css_class='col-md-4'),
                    ),
                ),
                css_class='form-section d-none',
                id='siz-section'
            ),

            # Скрытое поле для типа договора
            'contract_type',

            # Кнопки формы
            Div(
                Submit('submit', _('Сохранить'), css_class='btn-primary'),
                HTML(
                    '<a href="{% url "directory:hiring:hiring_list" %}" class="btn btn-secondary">{{ _("Отмена") }}</a>'),
                css_class='form-group text-right'
            )
        )

        # Ограничение организаций по профилю пользователя
        if self.user and hasattr(self.user, 'profile'):
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs

            # Если у пользователя одна организация, выбираем её по умолчанию
            if user_orgs.count() == 1:
                self.initial['organization'] = user_orgs.first().id

    def clean(self):
        """
        Валидация формы с проверкой динамических полей для медосмотра и СИЗ.
        """
        cleaned_data = super().clean()
        position = cleaned_data.get('position')

        # Если выбрана должность, определяем необходимость медосмотра и СИЗ
        if position:
            # Проверяем медосмотр (фильтруем по is_disabled=False)
            needs_medical = position.medical_factors.filter(is_disabled=False).exists()

            # Если не найдены переопределения, проверяем эталонные нормы медосмотра
            if not needs_medical:
                from directory.models.medical_norm import MedicalExaminationNorm
                needs_medical = MedicalExaminationNorm.objects.filter(
                    position_name=position.position_name
                ).exists()

            # Если требуется медосмотр, проверяем заполнение обязательных полей
            if needs_medical:
                date_of_birth = cleaned_data.get('date_of_birth')
                place_of_residence = cleaned_data.get('place_of_residence')

                if not date_of_birth:
                    self.add_error('date_of_birth', _('Необходимо указать дату рождения для медосмотра'))

                if not place_of_residence:
                    self.add_error('place_of_residence', _('Необходимо указать место проживания для медосмотра'))

            # Проверяем СИЗ
            needs_siz = position.siz_norms.exists()

            # Если нет переопределений, проверяем эталонные нормы СИЗ
            if not needs_siz:
                needs_siz = Position.find_reference_norms(position.position_name).exists()

            # Для СИЗ не делаем поля обязательными, но можно добавить валидацию при необходимости

        return cleaned_data