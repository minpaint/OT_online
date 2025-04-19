import logging
import datetime
import traceback
from typing import Dict, Any, Optional

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template,
    prepare_employee_context,
    generate_docx_from_template,
)

# Сервисные функции для работы с комиссией (экспортируемые из directory/utils/__init__.py)
from directory.utils import find_appropriate_commission, get_commission_members_formatted
# Для склонения названий в родительном падеже
from directory.utils.declension import decline_phrase

logger = logging.getLogger(__name__)


def generate_knowledge_protocol(
    employee,
    user=None,
    custom_context: Optional[Dict[str, Any]] = None
) -> Optional[GeneratedDocument]:
    """
    Генерирует протокол проверки знаний по вопросам охраны труда для сотрудника.
    """
    try:
        # 1) Шаблон
        template = get_document_template('knowledge_protocol', employee)
        if not template:
            raise ValueError("Не найден активный шаблон 'knowledge_protocol'")

        # 2) Базовый контекст
        context = prepare_employee_context(employee)

        # 3) Номер и дата протокола
        now = datetime.datetime.now()
        context.setdefault('protocol_number', f"PZ-{now.strftime('%Y%m%d')}-{employee.id}")
        context.setdefault('protocol_date', now.strftime("%d.%m.%Y"))

        # 4) Комиссия и её состав
        commission = find_appropriate_commission(employee)
        cdata = get_commission_members_formatted(commission) if commission else {}

        # 4.1) Председатель
        chairman = cdata.get('chairman', {})
        context.setdefault('chairman_name', chairman.get('name', '—'))
        context.setdefault('chairman_position', chairman.get('position', '—').lower())
        context.setdefault('chairman_name_initials', chairman.get('name_initials', '—'))

        # 4.2) Секретарь
        secretary = cdata.get('secretary', {})
        context.setdefault('secretary_name', secretary.get('name', '—'))
        context.setdefault('secretary_position', secretary.get('position', '—').lower())
        context.setdefault('secretary_name_initials', secretary.get('name_initials', '—'))

        # 4.3) Члены комиссии
        members = cdata.get('members_formatted', [])
        context.setdefault('members_formatted', members)

        # 4.4) Параграфы «ФИО – должность»
        members_paragraphs = [
            f"{m['name']} - {m['position'].lower()}"
            for m in members
        ]
        context['members_paragraphs'] = members_paragraphs

        # 4.5) Параграфы с инициалами
        members_initials_paragraphs = [
            m['name_initials'] for m in members
        ]
        context['members_initials_paragraphs'] = members_initials_paragraphs

        # 4.6) binding_name_genitive — «протокол комиссии чего…»
        if commission:
            if commission.department:
                binding = decline_phrase(commission.department.name, 'gent')
            elif commission.subdivision:
                binding = decline_phrase(commission.subdivision.name, 'gent')
            elif commission.organization:
                binding = decline_phrase(commission.organization.short_name_ru, 'gent')
            else:
                binding = ""
        else:
            binding = ""
        context.setdefault('binding_name_genitive', binding)

        # 5) Подмешать custom_context, если есть
        if custom_context:
            context.update(custom_context)

        logger.debug(f"[generate_knowledge_protocol] context keys: {list(context.keys())}")

        # 6) Рендерим и сохраняем
        result = generate_docx_from_template(template, context, employee, user)
        if not result:
            logger.error("generate_docx_from_template вернул None")
        return result

    except Exception:
        logger.error("Ошибка генерации протокола", exc_info=True)
        return None
