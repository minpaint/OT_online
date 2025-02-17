from django.contrib import admin
from directory.models import Department
from directory.forms.department import DepartmentForm

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    📂 Админ-класс для модели Department.
    """
    form = DepartmentForm
    list_display = ['name', 'short_name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name', 'short_name']

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Переопределяем get_form, чтобы передать request.user в форму (для миксина).
        """
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                # Передаем user в форму
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser
