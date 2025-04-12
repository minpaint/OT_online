# directory/document_generators/protocol_generator.py
"""
📄 Генератор для протокола проверки знаний
"""
import logging
import datetime
import traceback
from typing import Dict, Any, Optional

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_knowledge_protocol(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[GeneratedDocument]:
    """
    Генерирует протокол проверки знаний для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        template = get_document_template('knowledge_protocol', employee)
        if not template:
            logger.error("Активный шаблон для протокола проверки знаний не найден")
            raise ValueError("Активный шаблон для протокола проверки знаний не найден")

        context = prepare_employee_context(employee)

        now = datetime.datetime.now()
        context.setdefault('protocol_number', f"ПЗ-{now.strftime('%Y%m%d')}-{employee.id}")
        context.setdefault('protocol_date', now.strftime("%d.%m.%Y"))

        # Используем функцию get_commission_formatted для получения данных комиссии
        # Импорт здесь, чтобы избежать циклической зависимости
        from directory.views.documents.utils import get_commission_formatted
        commission_data, commission_success = get_commission_formatted(employee)

        # Устанавливаем значения по умолчанию, если данные комиссии не получены
        context.setdefault('commission_chairman', commission_data.get('chairman', 'Председатель комиссии'))
        context.setdefault('commission_members', commission_data.get('members', ['Член комиссии 1', 'Член комиссии 2']))
        context.setdefault('commission_secretary', commission_data.get('secretary', 'Секретарь комиссии'))

        context.setdefault('ticket_number', employee.id % 20 + 1 if employee.id else 1) # Добавлена проверка employee.id
        context.setdefault('test_result', 'прошел')

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        logger.info(f"Итоговый контекст для протокола: {list(context.keys())}")

        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Протокол проверки знаний успешно сгенерирован: {result.id}")
            return result
        else:
            logger.error("Ошибка при генерации протокола: функция generate_docx_from_template вернула None")
            return None

    except Exception as e:
        logger.error(f"Ошибка при генерации протокола проверки знаний: {str(e)}")
        logger.error(traceback.format_exc())
        return None
