from django.contrib import admin
from directory.models import Equipment
from directory.forms.equipment import EquipmentForm

@admin.register(Equipment)
class EquipmentAdmin(admin.ModelAdmin):
    """
    ⚙️ Админ-класс для модели Equipment.
    """
    form = EquipmentForm
    list_display = [
        'equipment_name',
        'inventory_number',
        'organization',
        'subdivision',
        'department'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)
        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)
        return FormWithUser

    def get_queryset(self, request):
        """
        🔒 Ограничиваем оборудование по организациям пользователя.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs
