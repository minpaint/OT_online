import logging
from typing import Optional, List
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from directory.models import Employee, GeneratedDocument
from directory.utils.hiring_utils import create_hiring_from_employee

logger = logging.getLogger(__name__)


def attach_documents_to_hiring(
        employee: Employee,
        document_ids: List[int],
        create_hiring_if_missing: bool = True,
        user=None
) -> Optional['EmployeeHiring']:
    """
    Прикрепляет сгенерированные документы к записи о приеме сотрудника.
    Если записи о приеме нет и create_hiring_if_missing=True, создает её.

    Args:
        employee: Объект сотрудника
        document_ids: Список ID сгенерированных документов
        create_hiring_if_missing: Создавать ли запись о приеме, если отсутствует
        user: Пользователь для создания записи

    Returns:
        Optional[EmployeeHiring]: Объект записи о приеме или None при ошибке
    """
    from directory.models import EmployeeHiring  # Импортируем здесь во избежание циклических импортов

    try:
        # Проверяем наличие записи о приеме
        hiring = None
        try:
            # Берем самую свежую запись о приеме
            hiring = EmployeeHiring.objects.filter(
                employee=employee,
                is_active=True
            ).order_by('-hiring_date').first()
        except ObjectDoesNotExist:
            hiring = None

        # Если нет записи и нужно создать
        if not hiring and create_hiring_if_missing:
            logger.info(f"Создание записи о приеме для сотрудника {employee.id}")
            hiring = create_hiring_from_employee(employee, user)

        if not hiring:
            logger.warning(f"Не найдена запись о приеме для сотрудника {employee.id}")
            return None

        # Прикрепляем документы
        with transaction.atomic():
            for doc_id in document_ids:
                try:
                    doc = GeneratedDocument.objects.get(id=doc_id)
                    hiring.documents.add(doc)
                    logger.info(f"Документ {doc_id} прикреплен к записи о приеме {hiring.id}")
                except ObjectDoesNotExist:
                    logger.warning(f"Документ {doc_id} не найден")

        return hiring

    except Exception as e:
        logger.error(f"Ошибка при прикреплении документов: {str(e)}")
        return None