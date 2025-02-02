class DependentFieldsMixin:
    dependent_fields = {}

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'directory/js/dependent_fields.js',
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.GET:
            for field, parent_field in self.dependent_fields.items():
                parent_value = request.GET.get(parent_field)
                if parent_value:
                    qs = qs.filter(**{parent_field: parent_value})
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            for child_field, parent_field in self.dependent_fields.items():
                if hasattr(obj, parent_field) and child_field in form.base_fields:
                    parent = getattr(obj, parent_field)
                    if parent:
                        form.base_fields[child_field].queryset = form.base_fields[child_field].queryset.filter(**{parent_field: parent})
        return form
