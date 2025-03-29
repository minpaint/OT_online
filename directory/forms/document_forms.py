"""
📝 Формы для работы с документами

Этот модуль содержит формы для выбора и настройки параметров документов.
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.forms import widgets
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, ButtonHolder, Submit, Div, HTML, Button, Field

from directory.models.document_template import DocumentTemplate
from directory.models import Employee


class DocumentSelectionForm(forms.Form):
    """
    Форма для выбора типа документа для генерации
    """
    document_type = forms.ChoiceField(
        label=_("Тип документа"),
        choices=DocumentTemplate.DOCUMENT_TYPES,
        widget=forms.RadioSelect,
        required=True
    )

    employee_id = forms.IntegerField(
        widget=forms.HiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'document-selection-form'
        self.helper.layout = Layout(
            'employee_id',
            Fieldset(
                _('Выберите тип документа для генерации'),
                Field('document_type'),
                css_class='mb-3'
            ),
            ButtonHolder(
                Submit('next', _('Далее'), css_class='btn-primary'),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )


class InternshipOrderForm(forms.Form):
    """
    Форма для настройки параметров распоряжения о стажировке
    """
    # Поля для редактирования шапки документа
    organization_name = forms.CharField(
        label=_("Наименование организации"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    location = forms.CharField(
        label=_("Место издания"),
        required=True,
        initial="г. Минск",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    order_date = forms.DateField(
        label=_("Дата распоряжения"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    order_number = forms.CharField(
        label=_("Номер распоряжения"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Поля для редактирования данных сотрудника
    fio_dative = forms.CharField(
        label=_("ФИО сотрудника (в дательном падеже)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    position_dative = forms.CharField(
        label=_("Должность (в дательном падеже)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    department = forms.CharField(
        label=_("Отдел"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    subdivision = forms.CharField(
        label=_("Структурное подразделение"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    internship_duration = forms.IntegerField(
        label=_("Продолжительность стажировки (дней)"),
        required=True,
        min_value=1,
        max_value=30,
        initial=2,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )

    # Поля для руководителя стажировки
    head_of_internship_position = forms.CharField(
        label=_("Должность руководителя стажировки"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    head_of_internship_name = forms.CharField(
        label=_("ФИО руководителя стажировки"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Должность и ФИО директора
    director_position = forms.CharField(
        label=_("Должность руководителя"),
        required=True,
        initial="Директор",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    director_name = forms.CharField(
        label=_("ФИО руководителя"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Сотрудники для ознакомления
    employee_name_initials = forms.CharField(
        label=_("ФИО сотрудника (сокращенно)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    head_of_internship_name_initials = forms.CharField(
        label=_("ФИО руководителя стажировки (сокращенно)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Добавляем скрытые поля для отслеживания иерархического уровня
    director_level = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    internship_leader_level = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        initial_data = kwargs.get('initial', {})
        self.employee = kwargs.pop('employee', None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'internship-order-form'

        # Создаем красивый макет для формы
        self.helper.layout = Layout(
            Fieldset(
                _('Основная информация'),
                Div(
                    Div('organization_name', css_class='col-md-8'),
                    Div('location', css_class='col-md-4'),
                    css_class='row'
                ),
                Div(
                    Div('order_date', css_class='col-md-6'),
                    Div('order_number', css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Информация о стажировке'),
                Div(
                    Div('fio_dative', css_class='col-md-6'),
                    Div('position_dative', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('department', css_class='col-md-4'),
                    Div('subdivision', css_class='col-md-4'),
                    Div('internship_duration', css_class='col-md-4'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Руководитель стажировки'),
                Div(
                    Div('head_of_internship_position', css_class='col-md-6'),
                    Div('head_of_internship_name', css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Подписи и ознакомление'),
                Div(
                    Div('director_position', css_class='col-md-6'),
                    Div('director_name', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('employee_name_initials', css_class='col-md-6'),
                    Div('head_of_internship_name_initials', css_class='col-md-6'),
                    css_class='row'
                ),
                'director_level',
                'internship_leader_level',
            ),
            ButtonHolder(
                Submit('preview', _('Предпросмотр'), css_class='btn-primary'),
                Submit('generate', _('Сгенерировать документ'), css_class='btn-success'),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )


class AdmissionOrderForm(forms.Form):
    """
    Форма для настройки параметров распоряжения о допуске к самостоятельной работе
    """
    # Поля для редактирования шапки документа
    organization_name = forms.CharField(
        label=_("Наименование организации"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    location = forms.CharField(
        label=_("Место издания"),
        required=True,
        initial="г. Минск",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    order_date = forms.DateField(
        label=_("Дата распоряжения"),
        required=True,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )

    order_number = forms.CharField(
        label=_("Номер распоряжения"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Поля для редактирования данных сотрудника
    fio_nominative = forms.CharField(
        label=_("ФИО сотрудника (именительный падеж)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    position_nominative = forms.CharField(
        label=_("Должность (именительный падеж)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    department = forms.CharField(
        label=_("Отдел"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    subdivision = forms.CharField(
        label=_("Структурное подразделение"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Должность и ФИО директора
    director_position = forms.CharField(
        label=_("Должность руководителя"),
        required=True,
        initial="Директор",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    director_name = forms.CharField(
        label=_("ФИО руководителя"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Сотрудники для ознакомления
    employee_name_initials = forms.CharField(
        label=_("ФИО сотрудника (сокращенно)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    head_of_internship_name_initials = forms.CharField(
        label=_("ФИО руководителя (сокращенно)"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Добавляем скрытые поля для отслеживания иерархического уровня
    director_level = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    internship_leader_level = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )

    def __init__(self, *args, **kwargs):
        initial_data = kwargs.get('initial', {})
        self.employee = kwargs.pop('employee', None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'admission-order-form'

        # Создаем красивый макет для формы
        self.helper.layout = Layout(
            Fieldset(
                _('Основная информация'),
                Div(
                    Div('organization_name', css_class='col-md-8'),
                    Div('location', css_class='col-md-4'),
                    css_class='row'
                ),
                Div(
                    Div('order_date', css_class='col-md-6'),
                    Div('order_number', css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Информация о допуске'),
                Div(
                    Div('fio_nominative', css_class='col-md-6'),
                    Div('position_nominative', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('department', css_class='col-md-6'),
                    Div('subdivision', css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Подписи и ознакомление'),
                Div(
                    Div('director_position', css_class='col-md-6'),
                    Div('director_name', css_class='col-md-6'),
                    css_class='row'
                ),
                Div(
                    Div('employee_name_initials', css_class='col-md-6'),
                    Div('head_of_internship_name_initials', css_class='col-md-6'),
                    css_class='row'
                ),
                'director_level',
                'internship_leader_level',
            ),
            ButtonHolder(
                Submit('preview', _('Предпросмотр'), css_class='btn-primary'),
                Submit('generate', _('Сгенерировать документ'), css_class='btn-success'),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )


class DocumentPreviewForm(forms.Form):
    """
    Форма для предпросмотра и редактирования документа перед генерацией
    """
    # Скрытое поле для хранения данных документа в формате JSON
    document_data = forms.CharField(widget=forms.HiddenInput)
    document_type = forms.CharField(widget=forms.HiddenInput)
    employee_id = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'document-preview-form'

        self.helper.layout = Layout(
            'document_data',
            'document_type',
            'employee_id',
            HTML('<div id="document-preview-container" class="mb-4"></div>'),
            ButtonHolder(
                Submit('generate', _('Сгенерировать документ'), css_class='btn-success'),
                Button('edit', _('Редактировать'), css_class='btn-primary',
                       onclick="enableEditing();"),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )