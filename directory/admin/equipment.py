# directory/admin/equipment.py
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.dateparse import parse_date

from directory.admin.mixins.tree_view import TreeViewMixin
from directory.models import Equipment
from directory.forms.equipment import EquipmentForm


class EquipmentTreeViewMixin(TreeViewMixin):
    """Расширяет TreeViewMixin, добавляя данные о ТО."""

    change_list_template = "admin/directory/equipment/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'item': '⚙️',
            'no_subdivision': '🏗️',
            'no_department': '📁',
        },
        'fields': {
            'name_field': 'equipment_name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False,
        }
    }

    # ────────────────────────────────────────────────────────────
    # ДАННЫЕ ДЛЯ ДЕРЕВА
    # ────────────────────────────────────────────────────────────
    def get_tree_data(self, request):
        """Добавляем информацию о следующих ТО в каждый `item`."""
        tree = super().get_tree_data(request)
        for org_data in tree.values():
            for item in org_data['items']:
                self._add_maintenance(item)
            for sub_data in org_data['subdivisions'].values():
                for item in sub_data['items']:
                    self._add_maintenance(item)
                for dept_data in sub_data['departments'].values():
                    for item in dept_data['items']:
                        self._add_maintenance(item)
        return tree

    # ────────────────────────────────────────────────────────────
    #  МЕТОДЫ ВСПОМОГАТЕЛЬНЫЕ
    # ────────────────────────────────────────────────────────────
    def _add_maintenance(self, item):
        """Записываем дату, дни до ТО и статус (только overdue/ok)."""
        obj = item['object']
        days = obj.days_until_maintenance()
        item.update({
            'next_maintenance_date': obj.next_maintenance_date,
            'days_to_maintenance': days,
            'maintenance_state': self._get_state(days),
        })

    @staticmethod
    def _get_state(days):
        """
        Возвращает статус обслуживания:
        - "overdue" - просрочено (дни < 0)
        - "warning" - скоро (0 <= дни <= 7)
        - "ok" - норма (дни > 7)
        - "unknown" - неизвестно (дни is None)
        """
        if days is None:
            return 'unknown'
        if days < 0:
            return 'overdue'
        if days <= 7:
            return 'warning'
        return 'ok'


@admin.register(Equipment)
class EquipmentAdmin(EquipmentTreeViewMixin, admin.ModelAdmin):
    form = EquipmentForm
    change_list_template = "admin/directory/equipment/change_list_tree.html"

    list_display = [
        'equipment_name', 'inventory_number',
        'organization', 'subdivision', 'department',
        'last_maintenance_date', 'next_maintenance_date'
    ]
    list_filter = ['organization', 'subdivision', 'department']
    search_fields = ['equipment_name', 'inventory_number']

    # ────────────────────────────────────────────────────────────
    #  ПЕРЕПРОВЕДЕНИЕ ТО ИЗ СПИСКА
    # ────────────────────────────────────────────────────────────
    def changelist_view(self, request, extra_context=None):
        # Обработка «Провести ТО» из дерева
        if request.method == 'POST' and 'perform_maintenance' in request.POST:
            pk = request.POST.get('perform_maintenance')
            date_str = request.POST.get(f'maintenance_date_{pk}')
            new_date = parse_date(date_str) if date_str else None
            obj = self.get_queryset(request).filter(pk=pk).first()
            if obj:
                obj.update_maintenance(new_date=new_date, comment='')
                self.message_user(request, f'ТО проведено для "{obj}"')
            return redirect(request.path)
        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(organization__in=allowed_orgs)
        return qs