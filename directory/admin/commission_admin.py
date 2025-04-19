# directory/admin/commission_admin.py

from django.contrib import admin
from django.utils.html import format_html
from dal import autocomplete
from directory.models import Commission, CommissionMember
from directory.admin.mixins.tree_view import TreeViewMixin


class CommissionMemberInline(admin.TabularInline):
    """Встроенная админка для участников комиссии"""
    model = CommissionMember
    extra = 1
    fields = ['employee', 'role', 'is_active']

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'employee':
            kwargs['widget'] = autocomplete.ModelSelect2(
                url='directory:employee-for-commission-autocomplete',
                forward=['commission', 'organization', 'subdivision', 'department']
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        if obj:
            formset.form.base_fields['employee'].widget.forward = [
                ('commission', obj.pk),
                ('organization', obj.organization_id or ''),
                ('subdivision', obj.subdivision_id or ''),
                ('department', obj.department_id or '')
            ]
        return formset


class CommissionTreeViewMixin(TreeViewMixin):
    change_list_template = "admin/directory/commission/change_list_tree.html"

    tree_settings = {
        'icons': {
            'organization': '🏢',
            'subdivision': '🏭',
            'department': '📂',
            'item': '🛡️',
            'ot': '🛡️',
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        },
        'fields': {
            'name_field': 'name',
            'organization_field': 'organization',
            'subdivision_field': 'subdivision',
            'department_field': 'department',
        },
        'display_rules': {
            'hide_empty_branches': False,
            'hide_no_subdivision_no_department': False
        }
    }

    def get_tree_data(self, request):
        tree = super().get_tree_data(request)
        self._enrich_tree_with_members(tree)
        return tree

    def _enrich_tree_with_members(self, tree):
        for org_data in tree.values():
            for item in org_data['items']:
                self._add_members_to_item(item)
            for sub_data in org_data['subdivisions'].values():
                for item in sub_data['items']:
                    self._add_members_to_item(item)
                for dept_data in sub_data['departments'].values():
                    for item in dept_data['items']:
                        self._add_members_to_item(item)

    def _add_members_to_item(self, item):
        obj = item['object']
        if hasattr(obj, 'members'):
            members = obj.members.filter(is_active=True).select_related('employee')
            roles = {
                'chairman': [],
                'secretary': [],
                'member': []
            }
            for member in members:
                roles[member.role].append({
                    'name': getattr(member.employee, 'full_name_nominative', str(member.employee)),
                    'position': getattr(member.employee, 'position_name', ''),
                    'role': member.get_role_display(),
                    'role_code': member.role
                })
            item['members'] = {
                'chairman': roles['chairman'],
                'secretary': roles['secretary'],
                'members': roles['member'],
                'total': len(members)
            }
            item['commission_type'] = obj.commission_type
            item['is_active'] = obj.is_active

    def _optimize_queryset(self, queryset):
        qs = super()._optimize_queryset(queryset)
        return qs.prefetch_related('members', 'members__employee')


@admin.register(Commission)
class CommissionAdmin(CommissionTreeViewMixin, admin.ModelAdmin):
    list_display = ['name', 'commission_type_display', 'level_display', 'members_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'commission_type', 'created_at']
    search_fields = ['name']
    inlines = [CommissionMemberInline]

    fieldsets = [
        (None, {'fields': ['name', 'commission_type', 'is_active']}),
        ('Привязка к структуре', {'fields': ['organization', 'subdivision', 'department']}),
    ]

    autocomplete_fields = ['organization']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            qs = qs.filter(
                organization__in=allowed_orgs
            ) | qs.filter(
                subdivision__organization__in=allowed_orgs
            ) | qs.filter(
                department__organization__in=allowed_orgs
            )
        return qs

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        form.base_fields['subdivision'].widget = autocomplete.ModelSelect2(
            url='directory:subdivision-autocomplete',
            forward=['organization']
        )

        form.base_fields['department'].widget = autocomplete.ModelSelect2(
            url='directory:department-autocomplete',
            forward=['subdivision']
        )

        if not request.user.is_superuser and hasattr(request.user, 'profile'):
            allowed_orgs = request.user.profile.organizations.all()
            form.base_fields['organization'].queryset = allowed_orgs

        return form

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        parent_obj = form.instance
        parent_obj.save()
        for instance in instances:
            instance.commission = parent_obj
            instance.save()
        for obj in formset.deleted_objects:
            obj.delete()
        formset.save_m2m()

    def commission_type_display(self, obj):
        icons = {
            'ot': '🛡️',
            'eb': '⚡',
            'pb': '🔥',
            'other': '📋'
        }
        icon = icons.get(obj.commission_type, '📋')
        return format_html('{} {}', icon, obj.get_commission_type_display())

    commission_type_display.short_description = 'Тип комиссии'

    def level_display(self, obj):
        return obj.get_level_display()

    level_display.short_description = 'Уровень'

    def members_count(self, obj):
        count = obj.members.filter(is_active=True).count()
        return count

    members_count.short_description = 'Участников'

    class Media:
        js = (
            'admin/js/commission_admin.js',
            'admin/js/tree_view.js',
        )
        css = {
            'all': ('admin/css/tree_view.css',)
        }
