# 📁 directory/forms.py
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

        if self.instance.pk and self.instance.organization:
            self.fields['subdivision'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.organization)
            )
            self.fields['department'].queryset = (
                Department.objects
                .filter(organization=self.instance.organization)
            )
            if self.instance.subdivision:
                self.fields['documents'].queryset = (
                    Document.objects
                    .filter(
                        organization=self.instance.organization,
                        subdivision=self.instance.subdivision
                    )
                )
                if self.instance.department:
                    self.fields['documents'].queryset = (
                        self.fields['documents'].queryset
                        .filter(department=self.instance.department)
                    )
                if self.instance.subdivision:
                    self.fields['equipment'].queryset = (
                        Equipment.objects
                        .filter(
                            organization=self.instance.organization,
                            subdivision=self.instance.subdivision
                        )
                    )
                    if self.instance.department:
                        self.fields['equipment'].queryset = (
                            self.fields['equipment'].queryset
                            .filter(department=self.instance.department)
                        )

    def clean(self):
        cleaned_data = super().clean()
        organization = cleaned_data.get('organization')
        subdivision = cleaned_data.get('subdivision')
        department = cleaned_data.get('department')

        if subdivision and subdivision.organization != organization:
            raise forms.ValidationError('Выбранное подразделение не принадлежит выбранной организации')

        if department:
            if department.organization != organization:
                raise forms.ValidationError('Выбранный отдел не принадлежит выбранной организации')
            if department.subdivision != subdivision:
                raise forms.ValidationError('Выбранный отдел не принадлежит выбранному подразделению')

        return cleaned_data

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

        if self.instance.pk and self.instance.position:
            self.fields['subdivision'].queryset = (
                StructuralSubdivision.objects
                .filter(organization=self.instance.position.organization)
            )
