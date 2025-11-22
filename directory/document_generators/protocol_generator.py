import logging
import datetime
import traceback
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Optional, List

from docxtpl import DocxTemplate
from django.conf import settings

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
) -> Optional[Dict[str, Any]]:
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
        # Базовый контекст уже содержит правильные значения для должности/работы по договору подряда
        # в полях position_nominative, position_genitive и т.д.

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

        # 4.4) Параграфы «ФИО – должность»
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
                # Название организации НЕ склоняется - это имя собственное в кавычках
                # "Комиссия ООО "Безопасность Плюс"", а не "ооо безопасности Плюс"
                binding = commission.organization.short_name_ru
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


def _find_periodic_table(docx_doc):
    """
    Locate the protocol results table by header keywords.
    """
    for table in docx_doc.tables:
        if not table.rows:
            continue
        header_text = " ".join(cell.text for cell in table.rows[0].cells)
        if "Результаты проверки знаний" in header_text and "Роспись" in header_text:
            return table
    return docx_doc.tables[-1] if docx_doc.tables else None


def _reset_periodic_table(table):
    """Remove all data rows keeping the header row only."""
    while len(table.rows) > 1:
        row = table.rows[-1]
        tbl = table._tbl
        tbl.remove(row._tr)


def _fill_periodic_rows(table, employees_data: List[Dict[str, str]]):
    """Append rows with employee data to the protocol table."""
    for idx, emp in enumerate(employees_data, start=1):
        row = table.add_row()
        cells = row.cells
        cols = len(cells)
        cells[0].text = str(idx)
        if cols > 1:
            cells[1].text = emp.get('fio_nominative', '')
        if cols > 2:
            cells[2].text = emp.get('position_nominative', '')
        if cols > 3:
            cells[3].text = "периодическая"
        if cols > 4:
            ticket = emp.get('ticket_number') or ""
            cells[4].text = str(ticket)
        if cols > 5:
            cells[5].text = ""
        if cols > 6:
            cells[6].text = ""


def generate_periodic_protocol(
    employees: List,
    user=None,
    custom_context: Optional[Dict[str, Any]] = None,
    grouping_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Сформировать протокол периодической проверки знаний для списка сотрудников.
    """
    try:
        if not employees:
            raise ValueError("Не переданы сотрудники для протокола")

        primary_employee = employees[0]
        template = get_document_template('periodic_protocol', primary_employee)
        fallback_path = Path(settings.MEDIA_ROOT) / 'document_templates' / 'etalon' / 'periodic_protocol_template.docx'
        if template:
            template_path = template.template_file.path
        elif fallback_path.exists():
            template_path = str(fallback_path)
        else:
            raise ValueError("Не найден активный шаблон 'periodic_protocol'")

        context = prepare_employee_context(primary_employee)
        now = datetime.datetime.now()
        context.setdefault('protocol_number', f"PP-{now.strftime('%Y%m%d')}-{primary_employee.id}")
        context.setdefault('protocol_date', now.strftime("%d.%m.%Y"))

        commission = find_appropriate_commission(primary_employee)
        cdata = get_commission_members_formatted(commission) if commission else {}

        chairman = cdata.get('chairman', {})
        context.setdefault('chairman_name', chairman.get('name', '-'))
        context.setdefault('chairman_position', chairman.get('position', '-').lower())
        context.setdefault('chairman_name_initials', chairman.get('name_initials', '-'))

        secretary = cdata.get('secretary', {})
        context.setdefault('secretary_name', secretary.get('name', '-'))
        context.setdefault('secretary_position', secretary.get('position', '-').lower())
        context.setdefault('secretary_name_initials', secretary.get('name_initials', '-'))

        members = cdata.get('members_formatted', [])
        context.setdefault('members_formatted', members)

        if grouping_name:
            binding = decline_phrase(grouping_name, 'gent')
        elif commission:
            if commission.department:
                binding = decline_phrase(commission.department.name, 'gent')
            elif commission.subdivision:
                binding = decline_phrase(commission.subdivision.name, 'gent')
            elif commission.organization:
                binding = commission.organization.short_name_ru
            else:
                binding = ""
        else:
            binding = context.get('organization_name_genitive', "")
        context.setdefault('binding_name_genitive', binding)

        if custom_context:
            context.update(custom_context)

        employees_data = []
        for idx, emp in enumerate(employees, start=1):
            emp_ctx = prepare_employee_context(emp)
            employees_data.append({
                'fio_nominative': emp_ctx.get('fio_nominative', ''),
                'position_nominative': emp_ctx.get('position_nominative', ''),
                'ticket_number': idx,
            })

        doc = DocxTemplate(template_path)
        render_context = context.copy()
        render_context.pop('employee', None)
        doc.render(render_context)

        table = _find_periodic_table(doc.docx)
        if table:
            _reset_periodic_table(table)
            _fill_periodic_rows(table, employees_data)

        buffer = BytesIO()
        doc.save(buffer)
        buffer.seek(0)

        filename = f"Протокол_периодической_проверки_{now.strftime('%Y%m%d')}.docx"
        return {'content': buffer.getvalue(), 'filename': filename}

    except Exception:
        logger.error("Ошибка формирования периодического протокола", exc_info=True)
        return None
