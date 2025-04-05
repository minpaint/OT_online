# D:\YandexDisk\OT_online\directory\forms\document_forms.py
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