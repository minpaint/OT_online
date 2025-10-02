# directory/admin/employee.py
from django.contrib import admin
from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import path
from django.http import HttpResponse
from tablib import Dataset

from directory.models import Employee
from directory.models.commission import CommissionMember
from directory.forms.employee import EmployeeForm
from directory.admin.mixins.tree_view import TreeViewMixin
from directory.resources.employee import EmployeeResource


@admin.register(Employee)
class EmployeeAdmin(TreeViewMixin, admin.ModelAdmin):
    """
    👤 Админ-класс для модели Employee с оптимизированным отображением.
    Показывает только ключевые атрибуты: Ответственный по ОТ, Руководитель 
    стажировки, Роль в комиссии, Статус.
    """
    form = EmployeeForm

    change_list_template = "admin/directory/employee/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'employee': '👤',
            'no_subdivision': '🏗️',
            'no_department': '📁'
        },
        'fields': {
            'name_field': 'name_with_position',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department'
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    list_display = [
        'full_name_nominative',
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
    ]
    list_filter = [
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
    ]
    search_fields = [
        'full_name_nominative',
        'position__position_name'
    ]

    fields = [
        'full_name_nominative',
        'date_of_birth',
        'place_of_residence',
        'organization',
        'subdivision',
        'department',
        'position',
        'contract_type',
        'status',
        'hire_date',
        'start_date',
        'height',
        'clothing_size',
        'shoe_size',
        'is_contractor',
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs.select_related(
            'organization',
            'subdivision',
            'department',
            'position'
        ).prefetch_related(
            'commission_roles',
            'commission_roles__commission'
        )

    def get_form(self, request, obj=None, **kwargs):
        Form = super().get_form(request, obj, **kwargs)

        class FormWithUser(Form):
            def __init__(self2, *args, **inner_kwargs):
                inner_kwargs['user'] = request.user
                super().__init__(*args, **inner_kwargs)

        return FormWithUser

    def get_urls(self):
        """🔗 Добавляем кастомные URL для импорта/экспорта"""
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_view), name='directory_employee_import'),
            path('export/', self.admin_site.admin_view(self.export_view), name='directory_employee_export'),
        ]
        return custom_urls + urls

    def get_node_additional_data(self, obj):
        """
        Получает дополнительные данные для отображения в дереве.
        Сокращенная версия с фокусом на ключевых атрибутах.
        """
        # Базовые данные о статусе
        additional_data = {
            'status': obj.status,
            'status_display': obj.get_status_display(),
            'status_emoji': self._get_status_emoji(obj.status),
        }

        # Атрибуты из позиции (должности)
        if obj.position:
            additional_data['is_responsible_for_safety'] = getattr(obj.position, 'is_responsible_for_safety', False)
            additional_data['can_be_internship_leader'] = getattr(obj.position, 'can_be_internship_leader', False)

        # Роли в комиссиях
        commission_roles = CommissionMember.objects.filter(
            employee=obj,
            is_active=True
        ).select_related('commission')

        # Для отображения в табличном виде сгруппируем роли
        additional_data['commission_roles'] = []
        for role in commission_roles:
            additional_data['commission_roles'].append({
                'commission_name': role.commission.name,
                'role': role.role,
                'role_display': role.get_role_display(),
                'role_emoji': self._get_commission_role_emoji(role.role)
            })

        return additional_data

    def _get_status_emoji(self, status):
        """Возвращает эмодзи для статуса сотрудника"""
        status_emojis = {
            'candidate': '📝',
            'active': '✅',
            'maternity_leave': '👶',
            'part_time': '⌛',
            'fired': '🚫',
        }
        return status_emojis.get(status, '❓')

    def _get_commission_role_emoji(self, role):
        """Возвращает эмодзи для роли в комиссии"""
        role_emojis = {
            'chairman': '🗳️',
            'secretary': '📝',
            'member': '👥'
        }
        return role_emojis.get(role, '❓')

    def import_view(self, request):
        """📥 Импорт сотрудников"""
        context = self.admin_site.each_context(request)

        if request.method == 'POST':
            if 'confirm' in request.POST:
                # Финальное подтверждение импорта
                dataset_data = request.session.get('employee_dataset')
                if not dataset_data:
                    messages.error(request, 'Данные для импорта не найдены. Загрузите файл заново.')
                    return redirect('admin:directory_employee_import')

                dataset = Dataset().load(dataset_data)
                resource = EmployeeResource()
                result = resource.import_data(dataset, dry_run=False)

                del request.session['employee_dataset']

                if result.has_errors():
                    # Выводим ошибки в консоль для отладки
                    print("="*80)
                    print("ОШИБКИ ИМПОРТА СОТРУДНИКОВ:")
                    print(f"Всего ошибок: {result.totals['error']}")
                    print(f"Invalid rows count: {len(result.invalid_rows)}")

                    for idx, row in enumerate(result.invalid_rows[:5]):
                        print(f"\n--- Строка {idx+1} ---")
                        print(f"Row object: {row}")
                        print(f"Row.__dict__: {row.__dict__ if hasattr(row, '__dict__') else 'N/A'}")
                        if hasattr(row, 'errors'):
                            for error in row.errors:
                                print(f"Error: {error.error}")
                                print(f"Traceback: {error.traceback}")

                    print(f"\nRow errors dict: {result.row_errors()}")
                    print("="*80)

                    messages.error(request, f'❌ Импорт завершен с ошибками! Создано: {result.totals["new"]}, ошибок: {result.totals["error"]}. Смотрите консоль сервера для деталей.')
                else:
                    messages.success(request, f'✅ Импорт завершен! Создано: {result.totals["new"]}, обновлено: {result.totals["update"]}')
                return redirect('admin:directory_employee_changelist')
            else:
                # Предпросмотр импорта
                import_file = request.FILES.get('import_file')
                if not import_file:
                    messages.error(request, 'Файл не выбран')
                    return redirect('admin:directory_employee_import')

                file_format = import_file.name.split('.')[-1].lower()
                if file_format not in ['xlsx', 'xls']:
                    messages.error(request, 'Поддерживаются только файлы XLSX и XLS')
                    return redirect('admin:directory_employee_import')

                try:
                    dataset = Dataset().load(import_file.read(), format=file_format)
                    resource = EmployeeResource()
                    result = resource.import_data(dataset, dry_run=True)

                    # Сохраняем данные в сессии для финального импорта
                    request.session['employee_dataset'] = dataset.export('json')

                    context.update({
                        'title': 'Предпросмотр импорта сотрудников',
                        'result': result,
                        'dataset': dataset,
                    })
                    return render(request, 'admin/directory/employee/import_preview.html', context)
                except Exception as e:
                    messages.error(request, f'Ошибка при обработке файла: {str(e)}')
                    return redirect('admin:directory_employee_import')

        context.update({
            'title': 'Импорт сотрудников',
            'subtitle': None,
        })
        return render(request, 'admin/directory/employee/import.html', context)

    def export_view(self, request):
        """📤 Экспорт сотрудников"""
        from directory.models import Employee

        # Фильтрация по организации (если указана)
        organization_id = request.GET.get('organization_id')

        if organization_id:
            queryset = Employee.objects.filter(organization_id=organization_id)
        else:
            queryset = Employee.objects.all()

        # Применяем права доступа
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            queryset = queryset.filter(organization__in=allowed_orgs)

        queryset = queryset.select_related('organization', 'subdivision', 'department', 'position')

        resource = EmployeeResource()
        dataset = resource.export(queryset)

        response = HttpResponse(
            dataset.export('xlsx'),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="employees.xlsx"'
        return response