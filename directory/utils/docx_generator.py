"""
📄 Модуль для генерации документов Word

Этот модуль содержит функции для работы с шаблонами DOCX и
генерации документов на основе данных из системы.
"""
import os
import uuid
import io
import logging
from typing import Dict, Any, Optional
import datetime
import traceback
from docxtpl import DocxTemplate
from django.conf import settings
from django.core.files.base import ContentFile

from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.utils.declension import decline_full_name, decline_phrase, get_initials_from_name

# Настройка логирования
logger = logging.getLogger(__name__)


def get_template_path(template_id: int) -> str:
    """
    Получает полный путь к файлу шаблона.
    Args:
        template_id (int): ID шаблона документа
    Returns:
        str: Полный путь к файлу шаблона
    Raises:
        FileNotFoundError: Если шаблон не найден
    """
    try:
        template = DocumentTemplate.objects.get(id=template_id)
        return os.path.join(settings.MEDIA_ROOT, str(template.template_file))
    except DocumentTemplate.DoesNotExist:
        raise FileNotFoundError(f"Шаблон с ID {template_id} не найден")


def prepare_employee_context(employee) -> Dict[str, Any]:
    """
    Подготавливает контекст с данными сотрудника для шаблона документа.
    Args:
        employee: Объект модели Employee
    Returns:
        Dict[str, Any]: Словарь с данными для заполнения шаблона
    """
    # Получаем текущую дату в разных форматах
    now = datetime.datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    day = now.strftime("%d")
    month = now.strftime("%m")
    year = now.strftime("%Y")
    year_short = now.strftime("%y")

    # Основной контекст данных сотрудника
    context = {
        # Основные данные сотрудника
        'employee': employee,
        # ФИО в разных падежах
        'fio_nominative': employee.full_name_nominative,
        'fio_genitive': decline_full_name(employee.full_name_nominative, 'gent'),
        'fio_dative': decline_full_name(employee.full_name_nominative, 'datv'),
        'fio_accusative': decline_full_name(employee.full_name_nominative, 'accs'),
        'fio_instrumental': decline_full_name(employee.full_name_nominative, 'ablt'),
        'fio_prepositional': decline_full_name(employee.full_name_nominative, 'loct'),
        # Сокращенное ФИО (Фамилия И.О.)
        'fio_initials': get_initials_from_name(employee.full_name_nominative),
        # Должность в разных падежах
        'position_nominative': employee.position.position_name if employee.position else "",
        'position_genitive': decline_phrase(employee.position.position_name, 'gent') if employee.position else "",
        'position_dative': decline_phrase(employee.position.position_name, 'datv') if employee.position else "",
        'position_accusative': decline_phrase(employee.position.position_name, 'accs') if employee.position else "",
        'position_instrumental': decline_phrase(employee.position.position_name, 'ablt') if employee.position else "",
        'position_prepositional': decline_phrase(employee.position.position_name, 'loct') if employee.position else "",
        # Подразделение и отдел
        'department': employee.department.name if employee.department else "",
        'department_genitive': decline_phrase(employee.department.name, 'gent') if employee.department else "",
        'department_dative': decline_phrase(employee.department.name, 'datv') if employee.department else "",
        'subdivision': employee.subdivision.name if employee.subdivision else "",
        'subdivision_genitive': decline_phrase(employee.subdivision.name, 'gent') if employee.subdivision else "",
        'subdivision_dative': decline_phrase(employee.subdivision.name, 'datv') if employee.subdivision else "",
        # Организация
        'organization_name': employee.organization.short_name_ru if employee.organization else "",
        'organization_full_name': employee.organization.full_name_ru if employee.organization else "",
        # Даты и номера документов
        'current_date': date_str,
        'current_day': day,
        'current_month': month,
        'current_year': year,
        'current_year_short': year_short,
        # Поля для номеров документов - заполняются отдельно
        'order_number': "",
        # Дополнительные поля
        'internship_duration': "2",  # Продолжительность стажировки в днях
        # Место нахождения (из организации)
        'location': employee.organization.location if employee.organization and hasattr(employee.organization, 'location') and employee.organization.location else "г. Минск",
    }

    # Добавляем поиск подписанта распоряжений
    from directory.views.documents.utils import get_document_signer

    signer, level, found = get_document_signer(employee)
    if found:
        context.update({
            'director_position': signer.position.position_name,
            'director_name': get_initials_from_name(signer.full_name_nominative),
            'director_level': level,  # Может пригодиться для отладки
        })
    else:
        # Значения по умолчанию, если подписант не найден
        context.update({
            'director_position': "Директор",
            'director_name': "И.И. Иванов",
        })

    return context


def generate_docx_from_template(template_id: int, context: Dict[str, Any],
                               employee, user=None) -> Optional[GeneratedDocument]:
    """
    Генерирует документ DOCX на основе шаблона и контекста данных.
    Args:
        template_id (int): ID шаблона документа
        context (Dict[str, Any]): Словарь с данными для заполнения шаблона
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        # Получаем шаблон
        template = DocumentTemplate.objects.get(id=template_id)
        template_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))

        # Проверяем существование файла шаблона
        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не найден: {template_path}")
            raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")

        # Загружаем шаблон
        doc = DocxTemplate(template_path)

        # Заполняем шаблон контекстом
        doc.render(context)

        # Создаем имя для сгенерированного файла
        filename = f"{template.document_type}_{employee.last_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        # Сохраняем в BytesIO буфер
        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)

        # Проверяем размер документа
        file_content = docx_buffer.getvalue()
        if len(file_content) == 0:
            logger.error(f"Создан пустой DOCX файл для {filename}")
            raise ValueError("Создан пустой DOCX файл")
        else:
            logger.info(f"Создан DOCX файл {filename}, размер: {len(file_content)} байт")

        # Создаем запись о сгенерированном документе
        generated_doc = GeneratedDocument()
        generated_doc.template = template
        generated_doc.employee = employee
        generated_doc.created_by = user
        generated_doc.document_data = context

        # Сохраняем файл с использованием ContentFile из буфера
        generated_doc.document_file.save(filename, ContentFile(file_content))
        generated_doc.save()

        return generated_doc

    except Exception as e:
        # Логирование ошибки с полной трассировкой
        logger.error(f"Ошибка при генерации документа: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def generate_internship_order(employee, user=None, custom_context=None):
    """
    Генерирует распоряжение о стажировке для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для распоряжения о стажировке
    try:
        template = DocumentTemplate.objects.get(document_type='internship_order', is_active=True)
    except DocumentTemplate.DoesNotExist:
        logger.error("Активный шаблон для распоряжения о стажировке не найден")
        raise ValueError("Активный шаблон для распоряжения о стажировке не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Ищем руководителя стажировки с иерархическим подходом
    from directory.views.documents.utils import get_internship_leader

    internship_leader, level, success = get_internship_leader(employee)
    if success and internship_leader:
        context.update({
            'head_of_internship_name': internship_leader.full_name_nominative,
            'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            'head_of_internship_position': internship_leader.position.position_name if hasattr(internship_leader, 'position') and internship_leader.position else "",
            'internship_leader_level': level,  # Добавляем для отладки
        })
    else:
        logger.warning(f"Не удалось найти руководителя стажировки для сотрудника {employee.full_name_nominative}")

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)


def generate_admission_order(employee, user=None, custom_context=None):
    """
    Генерирует распоряжение о допуске к самостоятельной работе для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для распоряжения о допуске
    try:
        template = DocumentTemplate.objects.get(document_type='admission_order', is_active=True)
    except DocumentTemplate.DoesNotExist:
        logger.error("Активный шаблон для распоряжения о допуске к самостоятельной работе не найден")
        raise ValueError("Активный шаблон для распоряжения о допуске к самостоятельной работе не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Ищем руководителя стажировки с иерархическим подходом (он же подписывает распоряжение о допуске)
    from directory.views.documents.utils import get_internship_leader

    internship_leader, level, success = get_internship_leader(employee)
    if success and internship_leader:
        context.update({
            'head_of_internship_name': internship_leader.full_name_nominative,
            'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            'head_of_internship_position': internship_leader.position.position_name if hasattr(internship_leader, 'position') and internship_leader.position else "",
            'internship_leader_level': level,  # Добавляем для отладки
        })
    else:
        logger.warning(f"Не удалось найти руководителя стажировки для сотрудника {employee.full_name_nominative}")

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)


def generate_knowledge_protocol(employee, user=None, custom_context=None):
    """
    Генерирует протокол проверки знаний для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для протокола знаний
    try:
        template = DocumentTemplate.objects.get(document_type='knowledge_protocol', is_active=True)
    except DocumentTemplate.DoesNotExist:
        logger.error("Активный шаблон для протокола проверки знаний не найден")
        raise ValueError("Активный шаблон для протокола проверки знаний не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Добавляем номер протокола
    now = datetime.datetime.now()
    context.update({
        'protocol_number': f"ПЗ-{now.strftime('%Y%m%d')}-{employee.id}",
        'protocol_date': now.strftime("%d.%m.%Y"),
    })

    # Получаем информацию о комиссии
    from directory.views.documents.utils import get_commission_members

    commission = get_commission_members(employee)
    if commission:
        context.update(commission)
    else:
        logger.warning(f"Не удалось получить информацию о комиссии для сотрудника {employee.full_name_nominative}")

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)


def generate_familiarization_document(employee, document_list=None, user=None, custom_context=None):
    """
    Генерирует лист ознакомления с документами для сотрудника.
    Args:
        employee: Объект модели Employee
        document_list: Список документов для ознакомления (опционально)
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для листа ознакомления
    try:
        template = DocumentTemplate.objects.get(document_type='doc_familiarization', is_active=True)
    except DocumentTemplate.DoesNotExist:
        logger.error("Активный шаблон для листа ознакомления не найден")
        raise ValueError("Активный шаблон для листа ознакомления не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Если список документов не указан, получаем список по умолчанию
    if not document_list:
        from directory.views.documents.utils import get_employee_documents
        document_list = get_employee_documents(employee)

    # Добавляем список документов
    context.update({
        'documents_list': document_list,
        'familiarization_date': context['current_date'],
    })

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)


def generate_all_orders(employee, user=None, document_data=None):
    """
    Генерирует комбинированное распоряжение для сотрудника.
    Включает стажировку и допуск к самостоятельной работе.

    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        document_data: Дополнительные данные для документа (опционально)

    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        # Получаем шаблон для комбинированного распоряжения
        template = get_document_template('all_orders')
        if not template:
            logger.error("Активный шаблон для комбинированного распоряжения не найден")
            raise ValueError("Активный шаблон для комбинированного распоряжения не найден")

        # Подготавливаем базовый контекст
        context = prepare_employee_context(employee)

        # Ищем руководителя стажировки с иерархическим подходом
        from directory.views.documents.utils import get_internship_leader

        internship_leader, level, success = get_internship_leader(employee)
        if success and internship_leader:
            context.update({
                'head_of_internship_name': internship_leader.full_name_nominative,
                'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
                'head_of_internship_position': internship_leader.position.position_name if hasattr(internship_leader, 'position') and internship_leader.position else "",
                'internship_leader_level': level,  # Добавляем для отладки
            })
        else:
            logger.warning(f"Не удалось найти руководителя стажировки для сотрудника {employee.full_name_nominative}")

        # Добавляем номера распоряжений
        now = datetime.datetime.now()
        context.update({
            'order_number': f"ОТ-{now.strftime('%Y%m%d')}-{employee.id}",
            'order_date': now.strftime("%d.%m.%Y"),
        })

        # Если есть дополнительные данные, добавляем их в контекст
        if document_data:
            context.update(document_data)

        # Генерируем документ
        return generate_docx_from_template(template.id, context, employee, user)

    except Exception as e:
        logger.error(f"Ошибка при генерации комбинированного распоряжения: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def get_document_template(document_type):
    """
    Получает шаблон документа определенного типа.
    Args:
        document_type (str): Тип документа ('internship_order', 'admission_order', 'knowledge_protocol', etc.)
    Returns:
        DocumentTemplate: Объект шаблона документа или None, если шаблон не найден
    Example:
        template = get_document_template('internship_order')
    """
    try:
        return DocumentTemplate.objects.get(document_type=document_type, is_active=True)
    except DocumentTemplate.DoesNotExist:
        logger.error(f"Шаблон документа типа '{document_type}' не найден")
        return None


def generate_document_from_template(template, employee, user=None, context=None):
    """
    Генерирует документ из шаблона и контекста.
    Args:
        template: Объект модели DocumentTemplate
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        context: Словарь с данными для заполнения шаблона (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    if not template:
        logger.error("Не указан шаблон документа")
        return None

    # Подготавливаем базовый контекст
    base_context = prepare_employee_context(employee)

    # Если есть дополнительный контекст, обновляем основной контекст
    if context:
        base_context.update(context)

    # Генерируем документ
    return generate_docx_from_template(template.id, base_context, employee, user)