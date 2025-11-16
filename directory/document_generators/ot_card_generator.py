# directory/document_generators/ot_card_generator.py
"""
📄 Генератор для личной карточки по охране труда (ОТ)
"""
import logging
import traceback
from typing import Dict, Any, Optional

from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_personal_ot_card(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """
    Генерирует личную карточку по охране труда.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[Dict]: Словарь с 'content' и 'filename' или None при ошибке
    """
    try:
        template = get_document_template('personal_ot_card', employee)
        if not template:
            logger.error("Активный шаблон для личной карточки по ОТ не найден")
            raise ValueError("Активный шаблон для личной карточки по ОТ не найден")

        context = prepare_employee_context(employee)

        # Добавляем специфичные для карточки ОТ поля
        context.setdefault('ot_card_number', f"OT-{employee.id}")
        context.setdefault('card_date', context.get('current_date')) # Используем базовую текущую дату

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        logger.info(f"Итоговый контекст для личной карточки ОТ: {list(context.keys())}")

        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Личная карточка по ОТ успешно сгенерирована: {result['filename']}")
            return result
        else:
            logger.error("Ошибка при генерации личной карточки по ОТ: функция generate_docx_from_template вернула None")
            return None

    except Exception as e:
        logger.error(f"Ошибка при генерации личной карточки по ОТ: {str(e)}")
        logger.error(traceback.format_exc())
        return None
