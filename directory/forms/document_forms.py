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
    Форма для выбора типов документов для генерации
    """
    document_types = forms.MultipleChoiceField(
        label=_("Типы документов"),
        choices=DocumentTemplate.DOCUMENT_TYPES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        help_text=_("Выберите один или несколько типов документов для генерации"),
        # Устанавливаем все типы документов по умолчанию
        initial=[doc_type[0] for doc_type in DocumentTemplate.DOCUMENT_TYPES]
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
                _('Выберите типы документов для генерации'),
                Field('document_types'),
                css_class='mb-3'
            ),
            ButtonHolder(
                Submit('next', _('Далее'), css_class='btn-primary'),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )


class AllOrdersForm(forms.Form):
    """
    Форма для настройки параметров распоряжений о стажировке (объединенный шаблон)
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

    def __init__(self, *args, **kwargs):
        initial_data = kwargs.get('initial', {})
        self.employee = kwargs.pop('employee', None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'all-orders-form'

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
            ),
            ButtonHolder(
                Submit('preview', _('Предпросмотр'), css_class='btn-primary'),
                Submit('generate', _('Сгенерировать документ'), css_class='btn-success'),
                Button('cancel', _('Отмена'), css_class='btn-secondary',
                       onclick="window.history.back();")
            )
        )


class SIZCardForm(forms.Form):
    """
    Форма для настройки параметров карточки учета СИЗ
    """
    # Здесь можно добавить дополнительные поля для настройки карточки СИЗ, если необходимо
    # Например, размеры СИЗ, которые не указаны в профиле сотрудника

    # Поля для редактирования шапки документа
    organization_name = forms.CharField(
        label=_("Наименование организации"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    employee_name = forms.CharField(
        label=_("ФИО сотрудника"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    position_name = forms.CharField(
        label=_("Должность"),
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    # Поля для размеров СИЗ
    height = forms.CharField(
        label=_("Рост"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    clothing_size = forms.CharField(
        label=_("Размер одежды"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    shoe_size = forms.CharField(
        label=_("Размер обуви"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    headgear_size = forms.CharField(
        label=_("Размер головного убора"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    respirator_size = forms.CharField(
        label=_("Размер СИЗОД"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    gloves_size = forms.CharField(
        label=_("Размер СИЗ рук"),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        initial_data = kwargs.get('initial', {})
        self.employee = kwargs.pop('employee', None)

        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_id = 'siz-card-form'

        # Создаем красивый макет для формы
        self.helper.layout = Layout(
            Fieldset(
                _('Основная информация'),
                Div(
                    Div('organization_name', css_class='col-md-12'),
                    css_class='row'
                ),
                Div(
                    Div('employee_name', css_class='col-md-6'),
                    Div('position_name', css_class='col-md-6'),
                    css_class='row'
                ),
            ),
            Fieldset(
                _('Размеры СИЗ'),
                Div(
                    Div('height', css_class='col-md-4'),
                    Div('clothing_size', css_class='col-md-4'),
                    Div('shoe_size', css_class='col-md-4'),
                    css_class='row'
                ),
                Div(
                    Div('headgear_size', css_class='col-md-4'),
                    Div('respirator_size', css_class='col-md-4'),
                    Div('gloves_size', css_class='col-md-4'),
                    css_class='row'
                ),
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