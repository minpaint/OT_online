# directory/document_generators/journal_example_generator.py
"""
📄 Генератор для образца заполнения журнала
"""
import logging
import traceback
from typing import Dict, Any, Optional

from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_journal_example(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Генерирует образец заполнения журнала.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[Dict]: Словарь с 'content' и 'filename' или None при ошибке
    """
    try:
        template = get_document_template('journal_example', employee)
        if not template:
            logger.error("Активный шаблон для образца заполнения журнала не найден")
            raise ValueError("Активный шаблон для образца заполнения журнала не найден")

        context = prepare_employee_context(employee)

        # Добавляем специфичные для образца журнала поля
        context.setdefault('journal_name', "Журнал регистрации инструктажей по охране труда") # Значение по умолчанию
        context.setdefault('journal_sample_date', context.get('current_date'))

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        logger.info(f"Итоговый контекст для образца журнала: {list(context.keys())}")

        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Образец заполнения журнала успешно сгенерирован: {result['filename']}")
            return result
        else:
            logger.error("Ошибка при генерации образца журнала: функция generate_docx_from_template вернула None")
            return None

    except Exception as e:
        logger.error(f"Ошибка при генерации образца заполнения журнала: {str(e)}")
        logger.error(traceback.format_exc())
        return None
