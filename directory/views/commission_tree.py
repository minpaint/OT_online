"""
🌳 Представление для древовидного отображения комиссий

Отображает иерархическую структуру комиссий:
Организация → Подразделения → Отделы → Комиссии (с участниками)
"""
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Prefetch

from directory.models import (
    Organization,
    Commission,
)
from directory.utils.commission_service import get_commission_members_formatted


class CommissionTreeView(LoginRequiredMixin, TemplateView):
    """
    🌳 Древовидное представление комиссий по организационной структуре.

    Отображает иерархическую структуру:
    Организация → Подразделение → Отдел → Комиссия (с участниками)
    """
    template_name = 'directory/commissions/tree_view.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Древовидная структура комиссий'

        # Получаем все организации, доступные пользователю
        user = self.request.user
        if hasattr(user, 'profile') and not user.is_superuser:
            allowed_orgs = user.profile.organizations.all()
        else:
            allowed_orgs = Organization.objects.all()

        # Создаем структуру данных для дерева
        tree_data = []

        # Оптимизируем запрос с использованием prefetch_related
        organizations = allowed_orgs.prefetch_related(
            'commissions',
            'commissions__members',
            'commissions__members__employee',
            'commissions__members__employee__position',
            'subdivisions',
            'subdivisions__commissions',
            'subdivisions__commissions__members',
            'subdivisions__commissions__members__employee',
            'subdivisions__commissions__members__employee__position',
            'subdivisions__departments',
            'subdivisions__departments__commissions',
            'subdivisions__departments__commissions__members',
            'subdivisions__departments__commissions__members__employee',
            'subdivisions__departments__commissions__members__employee__position',
        )

        # Иконки для типов комиссий
        commission_type_icons = {
            'ot': '🛡️',  # Охрана труда
            'eb': '⚡',  # Электробезопасность
            'pb': '🔥',  # Пожарная безопасность
            'other': '📋',  # Другие типы
        }

        # Иконки для ролей участников
        role_icons = {
            'chairman': '👑',
            'secretary': '📝',
            'member': '👤',
        }

        # Для каждой организации формируем структуру
        for org in organizations:
            org_data = {
                'id': org.id,
                'name': org.short_name_ru or org.full_name_ru,
                'icon': '🏢',
                'commissions': [],
                'subdivisions': []
            }

            # Получаем комиссии на уровне организации
            org_commissions = Commission.objects.filter(
                organization=org,
                subdivision__isnull=True,
                department__isnull=True
            ).prefetch_related(
                'members',
                'members__employee',
                'members__employee__position'
            )

            # Добавляем комиссии организации
            for commission in org_commissions:
                # Получаем участников комиссии в структурированном виде
                commission_data = get_commission_members_formatted(commission)

                # Тип комиссии и иконка
                commission_type = commission.commission_type
                type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                # Формируем данные комиссии
                comm_data = {
                    'id': commission.id,
                    'name': commission.name,
                    'icon': type_icon,
                    'is_active': commission.is_active,
                    'type': commission.get_commission_type_display(),
                    'level': 'organization',
                    'chairman': commission_data.get('chairman', {}),
                    'secretary': commission_data.get('secretary', {}),
                    'members': commission_data.get('members', []),
                }

                org_data['commissions'].append(comm_data)

            # Получаем подразделения организации
            subdivisions = org.subdivisions.all()

            # Для каждого подразделения получаем его комиссии и отделы
            for subdivision in subdivisions:
                subdiv_data = {
                    'id': subdivision.id,
                    'name': subdivision.name,
                    'icon': '🏭',
                    'commissions': [],
                    'departments': []
                }

                # Получаем комиссии на уровне подразделения
                subdiv_commissions = Commission.objects.filter(
                    organization=org,
                    subdivision=subdivision,
                    department__isnull=True
                ).prefetch_related(
                    'members',
                    'members__employee',
                    'members__employee__position'
                )

                # Добавляем комиссии подразделения
                for commission in subdiv_commissions:
                    commission_data = get_commission_members_formatted(commission)

                    # Тип комиссии и иконка
                    commission_type = commission.commission_type
                    type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                    # Формируем данные комиссии
                    comm_data = {
                        'id': commission.id,
                        'name': commission.name,
                        'icon': type_icon,
                        'is_active': commission.is_active,
                        'type': commission.get_commission_type_display(),
                        'level': 'subdivision',
                        'chairman': commission_data.get('chairman', {}),
                        'secretary': commission_data.get('secretary', {}),
                        'members': commission_data.get('members', []),
                    }

                    subdiv_data['commissions'].append(comm_data)

                # Получаем отделы подразделения
                departments = subdivision.departments.all()

                # Для каждого отдела получаем его комиссии
                for department in departments:
                    dept_data = {
                        'id': department.id,
                        'name': department.name,
                        'icon': '📂',
                        'commissions': []
                    }

                    # Получаем комиссии на уровне отдела
                    dept_commissions = Commission.objects.filter(
                        organization=org,
                        subdivision=subdivision,
                        department=department
                    ).prefetch_related(
                        'members',
                        'members__employee',
                        'members__employee__position'
                    )

                    # Добавляем комиссии отдела
                    for commission in dept_commissions:
                        commission_data = get_commission_members_formatted(commission)

                        # Тип комиссии и иконка
                        commission_type = commission.commission_type
                        type_icon = commission_type_icons.get(commission_type, commission_type_icons['other'])

                        # Формируем данные комиссии
                        comm_data = {
                            'id': commission.id,
                            'name': commission.name,
                            'icon': type_icon,
                            'is_active': commission.is_active,
                            'type': commission.get_commission_type_display(),
                            'level': 'department',
                            'chairman': commission_data.get('chairman', {}),
                            'secretary': commission_data.get('secretary', {}),
                            'members': commission_data.get('members', []),
                        }

                        dept_data['commissions'].append(comm_data)

                    # Добавляем отдел в подразделение, только если у него есть комиссии
                    if dept_data['commissions']:
                        subdiv_data['departments'].append(dept_data)

                # Добавляем подразделение в организацию, только если у него есть комиссии или отделы с комиссиями
                if subdiv_data['commissions'] or any(dept['commissions'] for dept in subdiv_data['departments']):
                    org_data['subdivisions'].append(subdiv_data)

            # Добавляем организацию в дерево, только если у нее есть комиссии или подразделения с комиссиями
            if org_data['commissions'] or any(
                    subdiv['commissions'] or subdiv['departments'] for subdiv in org_data['subdivisions']):
                tree_data.append(org_data)

        context['tree_data'] = tree_data
        context['commission_type_icons'] = commission_type_icons
        context['role_icons'] = role_icons

        return context