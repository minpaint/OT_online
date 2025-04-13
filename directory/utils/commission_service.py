# directory/utils/commission_service.py

import logging
from typing import Dict, List, Optional, Any
from directory.models import Employee, Commission, CommissionMember

# Настройка логирования
logger = logging.getLogger(__name__)


def find_appropriate_commission(employee: Employee) -> Optional[Commission]:
    """
    Автоматически находит подходящую комиссию для сотрудника по иерархии.

    Порядок поиска:
    1. Комиссия на уровне отдела (если сотрудник привязан к отделу)
    2. Комиссия на уровне подразделения (если сотрудник привязан к подразделению)
    3. Комиссия на уровне организации

    Args:
        employee: Объект модели Employee

    Returns:
        Optional[Commission]: Объект комиссии или None, если комиссия не найдена
    """
    if not employee:
        logger.warning("Функция find_appropriate_commission вызвана без сотрудника")
        return None

    logger.info(f"Поиск подходящей комиссии для сотрудника: {employee.full_name_nominative}")

    # Проверяем наличие комиссии на уровне отдела
    if employee.department:
        logger.debug(f"Поиск комиссии на уровне отдела: {employee.department.name}")
        commission = Commission.objects.filter(
            department=employee.department,
            is_active=True,
            commission_type='ot'  # По умолчанию ищем комиссию по охране труда
        ).first()

        if commission:
            logger.info(f"Найдена комиссия на уровне отдела: {commission.name}")
            return commission

    # Проверяем наличие комиссии на уровне подразделения
    if employee.subdivision:
        logger.debug(f"Поиск комиссии на уровне подразделения: {employee.subdivision.name}")
        commission = Commission.objects.filter(
            subdivision=employee.subdivision,
            is_active=True,
            commission_type='ot'
        ).first()

        if commission:
            logger.info(f"Найдена комиссия на уровне подразделения: {commission.name}")
            return commission

    # Проверяем наличие комиссии на уровне организации
    if employee.organization:
        logger.debug(f"Поиск комиссии на уровне организации: {employee.organization.short_name_ru}")
        commission = Commission.objects.filter(
            organization=employee.organization,
            is_active=True,
            commission_type='ot'
        ).first()

        if commission:
            logger.info(f"Найдена комиссия на уровне организации: {commission.name}")
            return commission

    logger.warning(f"Подходящая комиссия для сотрудника {employee.full_name_nominative} не найдена")
    return None


def get_initials_from_name(full_name: str) -> str:
    """
    Преобразует полное имя в формат с инициалами.
    Пример: "Иванов Иван Иванович" -> "И.И. Иванов"

    Args:
        full_name: Полное имя в формате "Фамилия Имя Отчество"

    Returns:
        str: Имя с инициалами
    """
    if not full_name:
        return ""

    parts = full_name.split()
    if len(parts) >= 3:
        return f"{parts[1][0]}.{parts[2][0]}. {parts[0]}"
    elif len(parts) == 2:
        return f"{parts[1][0]}. {parts[0]}"
    else:
        return full_name


def get_commission_members_formatted(commission: Commission) -> Dict[str, Any]:
    """
    Получает членов комиссии в структурированном формате для документов.

    Args:
        commission: Объект комиссии (Commission)

    Returns:
        dict: Словарь с данными о членах комиссии
    """
    if not commission:
        logger.warning("Не передан объект комиссии")
        return {}

    result = {
        'commission_name': commission.name,
        'commission_id': commission.id,
        'chairman': {},
        'secretary': {},
        'members': [],
        'members_formatted': []  # Список словарей с данными участников
    }

    # Получаем председателя
    chairman = commission.members.filter(
        role='chairman', is_active=True
    ).select_related('employee', 'employee__position').first()

    # Получаем секретаря
    secretary = commission.members.filter(
        role='secretary', is_active=True
    ).select_related('employee', 'employee__position').first()

    # Получаем членов комиссии
    members = commission.members.filter(
        role='member', is_active=True
    ).select_related('employee', 'employee__position').all()

    # Форматируем данные председателя
    if chairman:
        employee = chairman.employee
        position = employee.position.position_name if employee.position else ""
        name_initials = get_initials_from_name(employee.full_name_nominative)

        result['chairman'] = {
            'id': chairman.id,
            'employee_id': employee.id,
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials,
            'formatted': f"{name_initials}, {position.lower()}" if position else name_initials
        }

        # Добавляем в общий список для шаблона
        result['members_formatted'].append({
            'role': 'chairman',
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials
        })

    # Форматируем данные секретаря
    if secretary:
        employee = secretary.employee
        position = employee.position.position_name if employee.position else ""
        name_initials = get_initials_from_name(employee.full_name_nominative)

        result['secretary'] = {
            'id': secretary.id,
            'employee_id': employee.id,
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials,
            'formatted': f"{name_initials}, {position.lower()}" if position else name_initials
        }

        # Добавляем в общий список для шаблона
        result['members_formatted'].append({
            'role': 'secretary',
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials
        })

    # Форматируем данные членов комиссии
    for member in members:
        employee = member.employee
        position = employee.position.position_name if employee.position else ""
        name_initials = get_initials_from_name(employee.full_name_nominative)

        member_data = {
            'id': member.id,
            'employee_id': employee.id,
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials,
            'formatted': f"{name_initials}, {position.lower()}" if position else name_initials
        }

        result['members'].append(member_data)

        # Добавляем в общий список для шаблона
        result['members_formatted'].append({
            'role': 'member',
            'name': employee.full_name_nominative,
            'position': position,
            'name_initials': name_initials
        })

    return result