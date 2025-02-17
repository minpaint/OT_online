# 📁 directory/forms/organization.py
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from directory.models import Organization

class OrganizationForm(forms.ModelForm):
    """🏢 Форма для организаций"""

    class Meta:
        model = Organization
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 🎨 Crispy-forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', '💾 Сохранить'))
