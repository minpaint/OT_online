from django.contrib import admin
from directory.models import Employee
from directory.forms.employee import EmployeeForm

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee.
    """
    form = EmployeeForm
    list_display = [
        'full_name_nominative',
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor'
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'is_contractor'
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form, чтобы передать request.user в форму (для миксина).
        """
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser
