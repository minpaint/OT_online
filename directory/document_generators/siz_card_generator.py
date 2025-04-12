# directory/document_generators/siz_card_generator.py
"""
📄 Генератор для карточки СИЗ (Excel)
"""
import logging
import traceback
from typing import Dict, Any, Optional
from django.http import HttpRequest, HttpResponse # HttpResponse нужен для возвращаемого типа

# Настройка логирования
logger = logging.getLogger(__name__)

def generate_siz_card(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[HttpResponse]:
    """
    Генерирует карточку учета выдачи СИЗ в формате Excel.
    Args:
        employee: Объект модели Employee
        user: Пользователь, выполняющий действие (опционально)
        custom_context: Дополнительный контекст (не используется в этой функции,
                       но оставлен для унификации интерфейса)
    Returns:
        Optional[HttpResponse]: HTTP-ответ с Excel-файлом или None/ошибка при сбое.
                                Обратите внимание, возвращается HttpResponse, а не GeneratedDocument.
    """
    try:
        # Импорт здесь для избежания потенциальных проблем и зависимостей на старте
        from directory.views.documents.siz_integration import generate_siz_card_excel

        # Создаем фейковый HttpRequest, так как оригинальная функция его ожидает
        # Возможно, стоит рефакторить generate_siz_card_excel, чтобы она принимала employee и user напрямую
        request = HttpRequest()
        request.user = user
        request.method = 'GET' # Добавляем метод, может понадобиться во вложенной функции

        logger.info(f"Начало генерации карточки СИЗ для сотрудника ID: {employee.id}")
        # Не передаем custom_context, так как generate_siz_card_excel его не принимает
        response = generate_siz_card_excel(request, employee.id)
        logger.info(f"Карточка СИЗ успешно сгенерирована для сотрудника ID: {employee.id}")
        return response

    except ImportError as e:
        logger.error(f"Ошибка импорта при генерации карточки СИЗ: {e}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при генерации карточки СИЗ для сотрудника ID {employee.id}: {str(e)}")
        logger.error(traceback.format_exc())
        # В случае ошибки возвращаем None, чтобы соответствовать другим генераторам,
        # хотя можно вернуть и HttpResponse с ошибкой 500.
        return None
