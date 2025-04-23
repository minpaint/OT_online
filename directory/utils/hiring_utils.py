# directory/utils/hiring_utils.py
import logging
from typing import List, Optional

from django.conf import settings
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone

from directory.models import Employee, EmployeeHiring, GeneratedDocument
from directory.document_generators.base import prepare_employee_context

logger = logging.getLogger(__name__)


def create_hiring_from_employee(employee: Employee, user: Optional[User] = None) -> EmployeeHiring:
    """
    Создает запись о приеме на работу из существующего сотрудника
    """
    logger.info(f"Создание записи о приеме для сотрудника {employee.full_name_nominative}")

    # Определяем тип приема по contract_type
    hiring_type_map = {
        'standard': 'new',
        'contractor': 'contractor',
        'part_time': 'part_time',
        'transfer': 'transfer',
        'return': 'return',
    }

    hiring_type = hiring_type_map.get(getattr(employee, 'contract_type', 'standard'), 'new')

    # Создаем запись о приеме
    hiring = EmployeeHiring(
        employee=employee,
        hiring_date=getattr(employee, 'hire_date', timezone.now().date()),
        start_date=getattr(employee, 'start_date', timezone.now().date()),
        hiring_type=hiring_type,
        organization=employee.organization,
        subdivision=employee.subdivision,
        department=employee.department,
        position=employee.position,
        created_by=user
    )

    hiring.save()
    logger.info(f"Запись о приеме создана: ID={hiring.id}")

    # Связываем существующие документы сотрудника с записью о приеме
    if hasattr(employee, 'documents'):
        docs = employee.documents.all()
        hiring.documents.add(*docs)
        logger.info(f"Привязано {docs.count()} документов к записи о приеме")

    return hiring


def attach_document_to_hiring(hiring: EmployeeHiring, document: GeneratedDocument) -> bool:
    """
    Прикрепляет сгенерированный документ к записи о приеме
    """
    try:
        hiring.documents.add(document)
        logger.info(f"Документ {document.id} прикреплен к записи о приеме {hiring.id}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при прикреплении документа {document.id} к записи {hiring.id}: {e}")
        return False


@transaction.atomic
def bulk_create_hirings_from_employees(employees: List[Employee], user: Optional[User] = None) -> int:
    """
    Массовое создание записей о приеме для существующих сотрудников
    """
    created_count = 0
    for employee in employees:
        try:
            create_hiring_from_employee(employee, user)
            created_count += 1
        except Exception as e:
            logger.error(f"Ошибка при создании записи о приеме для {employee.id}: {e}")

    logger.info(f"Создано {created_count} записей о приеме из {len(employees)} сотрудников")
    return created_count