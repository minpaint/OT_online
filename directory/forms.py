from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column
from directory.models import (
    Organization,
    StructuralSubdivision,
    Department,
    Document,
    Equipment,
    Position,
    Employee
)

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

class StructuralSubdivisionForm(forms.ModelForm):
    class Meta:
        model = StructuralSubdivision
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        # Фильтруем доступные родительские подразделения
        if self.instance.pk and self.instance.organization:
            self.fields['parent'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.organization)
                .exclude(pk=self.instance.pk)
            )

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        # Фильтруем подразделения по выбранной организации
        if self.instance.pk and self.instance.organization:
            self.fields['subdivision'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.organization)
            )

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        # Фильтруем подразделения и отделы по выбранной организации
        if self.instance.pk and self.instance.organization:
            self.fields['subdivision'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.organization)
            )
            self.fields['department'].queryset = (
                Department.objects
                .filter(organization=self.instance.organization)
            )

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Сохранить'))

        # Если выбрана должность, фильтруем подразделения
        if self.instance.pk and self.instance.position:
            self.fields['subdivision'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.position.organization)
            )