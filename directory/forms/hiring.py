# directory/forms/hiring.py
from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone  # Не используется напрямую в этой форме, но может быть полезно для других
from django.db import transaction  # Не используется напрямую в этой форме
from django.forms import formset_factory  # Не используется напрямую в этой форме

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
    GeneratedDocument  # Не используется напрямую в этой форме
)
from directory.models.medical_norm import MedicalExaminationNorm  # Используется в clean


# from directory.utils.declension import decline_full_name # Не используется в этой форме, но в view
# from directory.forms.mixins import OrganizationRestrictionFormMixin # Не используется, т.к. логика в __init__


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
        queryset=Organization.objects.all(),  # Базовый queryset, будет уточнен в __init__ для пользователя
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
        queryset=StructuralSubdivision.objects.none(),  # Изначально пустой, будет заполнен в __init__
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
        queryset=Department.objects.none(),  # Изначально пустой, будет заполнен в __init__
        label=_("Отдел"),
        required=False,
        widget=autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision', 'organization'],
            # Добавил organization для большей точности, если отдел может быть без подразделения
            attrs={
                'data-placeholder': '📂 Выберите отдел...',
                'class': 'select2 form-control'
            }
        )
    )

    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),  # Базовый queryset
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
            format='%Y-%m-%d'  # Важно для корректного парсинга даты
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
        required=False,  # Если это всегда standard, можно сделать его нередактируемым
        widget=forms.HiddenInput()  # По умолчанию скрыто
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Настройка crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'hiring-form'
        self.helper.layout = Layout(
            Fieldset(
                _('Персональные данные'),
                Row(
                    Column('full_name_nominative', css_class='col-md-8'),
                    Column('hiring_type', css_class='col-md-4'),
                ),
                css_class='form-section'
            ),
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
            Div(
                Fieldset(
                    _('Информация для медосмотра'),
                    Row(
                        Column('date_of_birth', css_class='col-md-6'),
                        Column('place_of_residence', css_class='col-md-6'),
                    ),
                ),
                css_class='form-section d-none',  # Изначально скрыто
                id='medical-section'
            ),
            Div(
                Fieldset(
                    _('Информация для СИЗ'),
                    Row(
                        Column('height', css_class='col-md-4'),
                        Column('clothing_size', css_class='col-md-4'),
                        Column('shoe_size', css_class='col-md-4'),
                    ),
                ),
                css_class='form-section d-none',  # Изначально скрыто
                id='siz-section'
            ),
            'contract_type',  # Скрытое поле
            Div(
                Submit('submit', _('Сохранить'), css_class='btn-primary'),
                HTML(
                    '<a href="{% url "directory:hiring:hiring_list" %}" class="btn btn-secondary">{{ _("Отмена") }}</a>'),
                # Обратите внимание на тег Django, он будет работать только в шаблоне
                css_class='form-group text-right mt-3'  # Добавил mt-3 для отступа
            )
        )

        # Ограничение организаций по профилю пользователя
        if self.user and hasattr(self.user, 'profile') and not self.user.is_superuser:
            user_orgs = self.user.profile.organizations.all()
            self.fields['organization'].queryset = user_orgs
            # Установка initial значения для организации, если у пользователя только одна организация
            # и поле еще не было заполнено (например, при редактировании или ошибке валидации)
            if user_orgs.count() == 1 and not self.data.get('organization') and not self.initial.get('organization'):
                self.initial['organization'] = user_orgs.first().pk
        else:
            # Для суперпользователя или если нет профиля - все организации
            self.fields['organization'].queryset = Organization.objects.all()

        # Динамическое обновление queryset для зависимых полей
        # для корректной серверной валидации required=False полей.
        # Используем self.data если форма связана (POST), иначе self.initial (GET/пустая форма).

        # Сначала получаем ID организации. Оно может быть уже объектом, если форма была создана с initial={ 'organization': org_obj }
        # или строкой/числом, если из self.data или self.initial числового PK.
        organization_value = None
        if self.is_bound:  # Если форма связана с данными (например, из POST)
            organization_value = self.data.get('organization')
        elif self.initial:  # Если форма инициализирована с начальными данными
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
            self.fields['subdivision'].queryset = StructuralSubdivision.objects.filter(organization_id=organization_pk)
            self.fields['department'].queryset = Department.objects.filter(
                organization_id=organization_pk)  # Базовый фильтр для отдела
            self.fields['position'].queryset = Position.objects.filter(organization_id=organization_pk)

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
                # Уточняем queryset для отделов, если подразделение выбрано
                self.fields['department'].queryset = Department.objects.filter(
                    subdivision_id=subdivision_pk,
                    organization_id=organization_pk  # Дополнительная проверка на всякий случай
                )
                self.fields['position'].queryset = Position.objects.filter(
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
                    self.fields['position'].queryset = Position.objects.filter(
                        department_id=department_pk,
                        subdivision_id=subdivision_pk,  # Важно для точности
                        organization_id=organization_pk
                    )
                # Если отдел не выбран, но подразделение выбрано, должности фильтруются по подразделению
                # (уже сделано выше)
            else:
                # Если подразделение не выбрано, но организация выбрана,
                # показываем отделы без подразделения для этой организации.
                self.fields['department'].queryset = Department.objects.filter(
                    organization_id=organization_pk,
                    subdivision__isnull=True
                )
                # И должности без подразделения и отдела
                self.fields['position'].queryset = Position.objects.filter(
                    organization_id=organization_pk,
                    subdivision__isnull=True,
                    department__isnull=True
                )
        else:
            # Если организация не выбрана, зависимые поля должны иметь пустой queryset,
            # так как выбирать не из чего (это уже установлено при определении полей).
            # Но для position, если ничего не выбрано, можно оставить Position.objects.all()
            # или тоже .none(), в зависимости от желаемого поведения.
            # Текущее определение поля position - queryset=Position.objects.all()
            pass

    def clean(self):
        """
        Валидация формы с проверкой динамических полей для медосмотра и СИЗ.
        """
        cleaned_data = super().clean()
        position = cleaned_data.get('position')

        # Если выбрана должность, определяем необходимость медосмотра и СИЗ
        if position:
            # Проверяем медосмотр (фильтруем по is_disabled=False)
            # Убедимся, что у Position есть medical_factors (через PositionMedicalFactor)
            # и что у HarmfulFactor есть is_disabled
            # В вашем файле position.py есть medical_harmful_factors, но нет is_disabled напрямую на них.
            # Предположим, что фильтрация is_disabled происходит на уровне модели PositionMedicalFactor,
            # или что все факторы из position.medical_harmful_factors.all() считаются активными.
            # Для простоты, будем считать, что если есть факторы, то медосмотр нужен.
            # Если нужна более сложная логика с is_disabled, ее нужно реализовать в модели или здесь.

            # needs_medical = position.medical_harmful_factors.exists() # Простой вариант
            # Более точный вариант, если у PositionMedicalFactor есть поле is_active или is_disabled
            # needs_medical = position.positionmedicalfactor_set.filter(is_active=True).exists() # Пример

            # Используем логику из вашего исходного clean:
            needs_medical = False
            if hasattr(position, 'medical_factors') and hasattr(position.medical_factors,
                                                                'filter'):  # Проверка наличия менеджера
                needs_medical = position.medical_factors.filter(is_disabled=False).exists()

            # Если не найдены переопределения, проверяем эталонные нормы медосмотра
            if not needs_medical:
                # from directory.models.medical_norm import MedicalExaminationNorm # Импорт уже есть вверху
                needs_medical = MedicalExaminationNorm.objects.filter(
                    position_name=position.position_name  # Предполагаем, что MedicalExaminationNorm имеет position_name
                ).exists()

            # Если требуется медосмотр, проверяем заполнение обязательных полей
            if needs_medical:
                date_of_birth = cleaned_data.get('date_of_birth')
                place_of_residence = cleaned_data.get('place_of_residence')

                if not date_of_birth:
                    self.add_error('date_of_birth', _('Необходимо указать дату рождения для медосмотра.'))

                if not place_of_residence:
                    self.add_error('place_of_residence', _('Необходимо указать место проживания для медосмотра.'))

            # Проверяем СИЗ
            needs_siz = False
            if hasattr(position, 'siz_norms') and hasattr(position.siz_norms, 'exists'):  # Проверка наличия менеджера
                needs_siz = position.siz_norms.exists()

            # Если нет переопределений, проверяем эталонные нормы СИЗ
            if not needs_siz:
                # Используем метод модели Position, если он есть
                if hasattr(Position, 'find_reference_norms'):
                    needs_siz = Position.find_reference_norms(position.position_name).exists()
                else:  # Запасной вариант, если метода нет
                    # Тут нужна логика поиска эталонных норм СИЗ, если она отличается
                    pass

                    # Для СИЗ не делаем поля обязательными в этом примере,
            # но можно добавить валидацию при необходимости (например, если needs_siz=True, то рост/размер должны быть).

        return cleaned_data


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
                employee_id=employee_id  # Предполагается, что у GeneratedDocument есть ForeignKey на Employee
            ).order_by('-created_at')

            # Добавляем аннотацию типа документа для более понятного отображения
            self.fields[
                'documents'].label_from_instance = self.label_from_instance_custom  # Переименовал, чтобы не конфликтовать с возможным родительским

    @staticmethod
    def label_from_instance_custom(obj):  # Переименовал
        """Форматирует метку для документа в списке"""
        if hasattr(obj, 'template') and obj.template and hasattr(obj.template, 'get_document_type_display'):
            type_name = obj.template.get_document_type_display()
            created_at_str = obj.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(obj,
                                                                                  'created_at') and obj.created_at else "N/A"
            return f"{type_name} ({created_at_str})"
        created_at_str_default = obj.created_at.strftime('%d.%m.%Y') if hasattr(obj,
                                                                                'created_at') and obj.created_at else "N/A"
        return f"Документ #{obj.id} ({created_at_str_default})"