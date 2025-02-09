from django.contrib import admin
from directory.models.department import Department
from directory.forms import DepartmentForm

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """
    📂 Админ-класс для модели Department.
    При добавлении нового отдела пользователь выбирает организацию, затем подразделение.
    """
    form = DepartmentForm
    list_display = ['name', 'short_name', 'organization', 'subdivision']
    list_filter = ['organization', 'subdivision']
    search_fields = ['name', 'short_name']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization', 'subdivision')