from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from directory.models import StructuralSubdivision
from directory.forms.subdivision import StructuralSubdivisionForm

@admin.register(StructuralSubdivision)
class StructuralSubdivisionAdmin(MPTTModelAdmin):
    """
    🏭 Админ-класс для модели StructuralSubdivision.
    """
    form = StructuralSubdivisionForm
    mptt_indent_field = "name"
    list_display = ('indented_title_display', 'organization',)
    list_filter = ['organization']
    search_fields = ['name', 'short_name']

    def indented_title_display(self, obj):
        """
        🔍 Отображает название подразделения с отступами, соответствующими уровню иерархии.
        """
        indent = "&nbsp;" * (obj.level * 4)
        return admin.utils.format_html("{}{}", indent, obj.name)
    indented_title_display.short_description = "Наименование подразделения"

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
