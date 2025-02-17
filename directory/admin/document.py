from django.contrib import admin
from directory.models import Document
from directory.forms.document import DocumentForm

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    📄 Админ-класс для модели Document.
    """
    form = DocumentForm
    list_display = ['name', 'organization', 'subdivision', 'department']
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['name']

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
