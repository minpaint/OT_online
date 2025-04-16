# directory/document_generators/protocol_generator.py

import logging
import datetime
import traceback
from typing import Dict, Any, Optional

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)

# Импортируем сервисы для работы с комиссией
from directory.utils.commission_service import (
    find_appropriate_commission,
    get_commission_members_formatted
)

# Для склонения ФИО и должностей
from directory.utils.declension import decline_full_name, decline_phrase

logger = logging.getLogger(__name__)


def generate_knowledge_protocol(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[
    GeneratedDocument]:
    """
    Генерирует протокол проверки знаний по вопросам охраны труда для сотрудника.

    Args:
        employee: Объект модели Employee.
        user: Пользователь, создающий документ (опционально).
        custom_context: Пользовательский контекст (опционально).

    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке.
    """
    try:
        # 1) Находим активный шаблон "knowledge_protocol"
        template = get_document_template('knowledge_protocol', employee)
        if not template:
            logger.error("Активный шаблон для протокола проверки знаний не найден")
            raise ValueError("Активный шаблон для протокола проверки знаний не найден")

        # 2) Получаем базовый контекст из данных сотрудника
        context = prepare_employee_context(employee)

        # 3) Дополняем контекст информацией о протоколе
        now = datetime.datetime.now()
        context.setdefault('protocol_number', f"ПЗ-{now.strftime('%Y%m%d')}-{employee.id}")
        context.setdefault('protocol_date', now.strftime("%d.%m.%Y"))

        if employee.organization:
            context.setdefault('organization_name', employee.organization.short_name_ru)
        else:
            context.setdefault('organization_name', "—")

        context.setdefault('fio_nominative', employee.full_name_nominative or "—")

        if employee.position and employee.position.position_name:
            context.setdefault('position_nominative', employee.position.position_name)
        else:
            context.setdefault('position_nominative', "")

        context.setdefault('ticket_number', (employee.id % 20 + 1) if employee.id else 1)
        context.setdefault('test_result', 'прошел')

        # 4) Находим комиссию для сотрудника и получаем её состав
        commission = find_appropriate_commission(employee)
        if commission:
            cdata = get_commission_members_formatted(commission)
        else:
            cdata = {}

        # 4.1) Председатель комиссии – должность приводим к нижнему регистру
        chairman = cdata.get('chairman', {})
        context.setdefault('chairman_name', chairman.get('name', '—'))
        context.setdefault('chairman_position', chairman.get('position', '—').lower())
        context.setdefault('chairman_name_initials', chairman.get('name_initials', '—'))

        # 4.2) Секретарь комиссии – аналогично (должность приводим к нижнему регистру)
        secretary = cdata.get('secretary', {})
        context.setdefault('secretary_name', secretary.get('name', '—'))
        context.setdefault('secretary_position', secretary.get('position', '—').lower())
        context.setdefault('secretary_name_initials', secretary.get('name_initials', '—'))

        # 4.3) Оставляем исходный список членов комиссии для обратной совместимости
        context.setdefault('members_formatted', cdata.get('members_formatted', []))

        # 4.4) Формируем два отдельных списка:
        # - members_paragraphs – строки вида "ФИО - должность" (должность в нижнем регистре),
        # - members_initials_paragraphs – строки с инициалами.
        members_data = cdata.get('members_formatted', [])
        members_paragraphs = []
        members_initials_paragraphs = []
        for m in members_data:
            full_name = m.get('name', '—')
            pos_lower = m.get('position', '—').lower()
            initials = m.get('name_initials', '—')
            line_full = f"{full_name} - {pos_lower}"
            line_initials = f"{initials}"
            members_paragraphs.append(line_full)
            members_initials_paragraphs.append(line_initials)
        context['members_paragraphs'] = members_paragraphs
        context['members_initials_paragraphs'] = members_initials_paragraphs

        # 4.5) Вычисляем заглушку для привязки комиссии (binding_name_genitive)
        if commission:
            if commission.department:
                binding_name = decline_phrase(commission.department.name, 'gent')
            elif commission.subdivision:
                binding_name = decline_phrase(commission.subdivision.name, 'gent')
            elif commission.organization:
                binding_name = decline_phrase(commission.organization.short_name_ru, 'gent')
            else:
                binding_name = ""
        else:
            binding_name = ""
        context.setdefault('binding_name_genitive', binding_name)

        # 5) Если пользователь передал дополнительные данные, обновляем контекст
        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        logger.info(f"[generate_knowledge_protocol] Итоговый контекст для протокола: {context}")

        # 6) Генерируем документ DOCX
        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Протокол проверки знаний успешно сгенерирован: GeneratedDocument.id={result.id}")
            return result
        else:
            logger.error("Ошибка: generate_docx_from_template вернул None")
            return None

    except Exception as e:
        logger.error(f"Ошибка при генерации протокола проверки знаний: {str(e)}")
        logger.error(traceback.format_exc())
        return None
