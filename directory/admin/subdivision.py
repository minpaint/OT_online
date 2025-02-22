from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from directory.models import StructuralSubdivision
from directory.forms.subdivision import StructuralSubdivisionForm

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(MPTTModelAdmin):
    """
    🏭 Админ-класс для модели StructuralSubdivision.
    Отображает древовидный список (в change‑list) с отступами, используя MPTTModelAdmin.
    """
    form = StructuralSubdivisionForm
    mptt_indent_field = "name"
    list_display = ('indented_title_display', 'organization',)
    list_filter = ['organization']
    search_fields = ['name', 'short_name']

    def indented_title_display(self, obj):
        # Создаем отступы в зависимости от уровня узла
        indent = "&nbsp;" * (obj.level * 4)
        return admin.utils.format_html("{}{}", indent, obj.name)
    indented_title_display.short_description = "Наименование подразделения"

    def get_form(self, request, obj=None, **kwargs):
        """
        Переопределяем get_form для передачи request.user в форму.
        Это позволяет применять логику ограничения по организациям.
        """
        Form = super().get_form(request, obj, **kwargs)
        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)
        return FormWithUser

    def get_queryset(self, request):
        """
        🔒 Ограничиваем подразделения по организациям, доступным пользователю.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs
