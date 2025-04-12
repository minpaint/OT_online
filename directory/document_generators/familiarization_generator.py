# directory/document_generators/familiarization_generator.py
"""
📄 Генератор для листа ознакомления
"""
import logging
import traceback
from typing import Dict, Any, Optional, List

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_familiarization_document(
    employee,
    document_list: Optional[List[Dict[str, Any]]] = None,
    user=None,
    custom_context: Optional[Dict[str, Any]] = None
) -> Optional[GeneratedDocument]:
    """
    Генерирует лист ознакомления для сотрудника.
    Args:
        employee: Объект модели Employee
        document_list: Список документов для ознакомления (опционально)
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        template = get_document_template('doc_familiarization', employee)
        if not template:
            logger.error("Активный шаблон для листа ознакомления не найден")
            raise ValueError("Активный шаблон для листа ознакомления не найден")

        context = prepare_employee_context(employee)

        # Получаем список документов, если он не передан
        if document_list is None:
            # Импорт здесь, чтобы избежать циклической зависимости
            from directory.views.documents.utils import get_employee_documents
            fetched_list, success = get_employee_documents(employee)
            if success:
                document_list = fetched_list
            else:
                logger.warning(f"Не удалось получить список документов для сотрудника {employee.id}")
                document_list = [] # Используем пустой список по умолчанию

        context.update({
            'documents_list': document_list,
            'familiarization_date': context.get('current_date'), # Используем уже подготовленную дату
        })

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        logger.info(f"Итоговый контекст для листа ознакомления: {list(context.keys())}")

        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Лист ознакомления успешно сгенерирован: {result.id}")
            return result
        else:
            logger.error("Ошибка при генерации листа ознакомления: функция generate_docx_from_template вернула None")
            return None

    except Exception as e:
        logger.error(f"Ошибка при генерации листа ознакомления: {str(e)}")
        logger.error(traceback.format_exc())
        return None
