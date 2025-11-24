# directory/utils/commission_service.py

import logging
from typing import Dict, Optional

from directory.models import Commission, Employee
from directory.utils.declension import get_initials_before_surname  # Формат "И.О. Фамилия" для комиссий

logger = logging.getLogger(__name__)

def find_appropriate_commission(employee: Employee, commission_type: str = "ot") -> Optional[Commission]:
    """
    Находит подходящую комиссию для сотрудника по иерархии:
      1. Отдел (department)
      2. Подразделение (subdivision) без конкретного отдела
      3. Организация (organization), без subdivision/department
    """
    # Уровень 1: Ищем комиссию на уровне отдела
    if employee.department_id:
        commission = Commission.objects.filter(
            organization_id=employee.organization_id,
            subdivision_id=employee.subdivision_id,
            department_id=employee.department_id,
            commission_type=commission_type,
            is_active=True
        ).first()
        if commission:
            logger.debug(f"Найдена комиссия на уровне отдела: {commission}")
            return commission

    # Уровень 2: Ищем комиссию на уровне подразделения (без отдела)
    if employee.subdivision_id:
        commission = Commission.objects.filter(
            organization_id=employee.organization_id,
            subdivision_id=employee.subdivision_id,
            department__isnull=True,
            commission_type=commission_type,
            is_active=True
        ).first()
        if commission:
            logger.debug(f"Найдена комиссия на уровне подразделения: {commission}")
            return commission

    # Уровень 3: Ищем комиссию на уровне организации (без подразделения и отдела)
    if employee.organization_id:
        commission = Commission.objects.filter(
            organization_id=employee.organization_id,
            subdivision__isnull=True,
            department__isnull=True,
            commission_type=commission_type,
            is_active=True
        ).first()
        if commission:
            logger.debug(f"Найдена комиссия на уровне организации: {commission}")
            return commission

    logger.debug("Подходящая комиссия не найдена.")
    return None


def get_commission_members_formatted(commission: Commission) -> Dict[str, any]:
    """
    Формирует состав комиссии с разбивкой по ролям:
      - chairman (председатель)
      - secretary (секретарь)
      - members (список остальных)
      - members_formatted (то же самое, чаще для шаблонов)
    """
    chairman_data = {}
    secretary_data = {}
    members_data = []

    # Загружаем всех участников комиссии
    for member in commission.members.filter(is_active=True).select_related('employee', 'employee__position'):
        full_name = member.employee.full_name_nominative or ""
        initials = get_initials_before_surname(full_name)  # Формат "И.О. Фамилия"
        position = member.employee.position.position_name if member.employee.position else ""

        entry = {
            'role': member.role,
            'name': full_name,
            'name_initials': initials,
            'position': position
        }
        if member.role == 'chairman':
            chairman_data = entry
        elif member.role == 'secretary':
            secretary_data = entry
        else:
            members_data.append(entry)

    return {
        'chairman': chairman_data,
        'secretary': secretary_data,
        'members': members_data,
        'members_formatted': members_data
    }
