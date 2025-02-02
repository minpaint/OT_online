from django.contrib import admin
from directory.models.employee import Employee


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = [
        'full_name_nominative',
        'date_of_birth',
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
        'is_contractor',
        'clothing_size',
        'shoe_size'
    ]
    search_fields = [
        'full_name_nominative',
        'full_name_dative',
        'position__position_name'
    ]
    autocomplete_fields = ['organization']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'full_name_nominative',
                'full_name_dative',
                'date_of_birth',
                'place_of_residence',
                'is_contractor'
            )
        }),
        ('Иерархия', {
            'fields': (
                'organization',
                'subdivision',
                'department',
                'position'
            )
        }),
        ('Размеры', {
            'fields': (
                'height',
                'clothing_size',
                'shoe_size'
            ),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'organization', 'subdivision', 'department', 'position'
        )