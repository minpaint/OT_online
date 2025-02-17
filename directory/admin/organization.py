from django.contrib import admin
from directory.models import Organization
from directory.forms.organization import OrganizationForm

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """
    🏢 Админ-класс для модели Organization.
    """
    form = OrganizationForm
    list_display = ['full_name_ru', 'short_name_ru', 'full_name_by', 'short_name_by']
    search_fields = ['full_name_ru', 'short_name_ru', 'full_name_by', 'short_name_by']

    def get_form(self, request, obj=None, **kwargs):
        """
        🔑 Если нужно фильтровать Organizations по профилю, сделайте аналогично другим моделям.
        Но обычно админы видят все организации.
        """
        return super().get_form(request, obj, **kwargs)
