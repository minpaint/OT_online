# directory/utils/docx_generator.py
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


def get_document_template(document_type, employee=None):
    """
    Получает шаблон документа с учетом организации сотрудника.

    Порядок поиска:
    1. Если сотрудник принадлежит организации, ищется шаблон, привязанный к этой организации.
    2. Если не найден, ищется эталонный шаблон (is_default=True).
    3. Если ни один из вариантов не найден, возвращается None.

    Args:
        document_type (str): Тип документа.
        employee (Employee, optional): Сотрудник, для которого выбирается шаблон.

    Returns:
        DocumentTemplate: Объект шаблона документа или None, если шаблон не найден.
    """
    # Получаем все активные шаблоны данного типа
    templates = DocumentTemplate.objects.filter(
        document_type=document_type,
        is_active=True
    )

    # Если сотрудник принадлежит организации, ищем шаблон для этой организации
    if employee and employee.organization:
        org_template = templates.filter(organization=employee.organization).first()
        if org_template:
            logger.info(f"Найден шаблон для организации {employee.organization.short_name_ru}: {org_template.name}")
            return org_template

    # Если не найден шаблон для организации, ищем эталонный шаблон
    default_template = templates.filter(is_default=True).first()
    if default_template:
        logger.info(f"Найден эталонный шаблон: {default_template.name}")
        return default_template

    logger.error(f"Шаблон документа типа '{document_type}' не найден")
    return None

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
        'fio_dative': employee.full_name_dative,  # Используем уже готовое поле из модели
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
        'internship_duration': getattr(employee.position, 'internship_period_days', 2) if employee.position else "2",
        # Место нахождения (из организации)
        'location': employee.organization.location if employee.organization and hasattr(employee.organization, 'location') and employee.organization.location else "г. Минск",
        # Поля для отображения в шаблоне
        'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
    }

    # Добавляем поиск подписанта распоряжений
    from directory.views.documents.utils import get_document_signer

    signer, level, found = get_document_signer(employee)
    if found and signer:
        context.update({
            'director_position': signer.position.position_name if signer.position else "Директор",
            'director_name': signer.full_name_nominative,
            'director_name_initials': get_initials_from_name(signer.full_name_nominative),
            'director_level': level,  # Может пригодиться для отладки
        })
    else:
        # Значения по умолчанию, если подписант не найден
        context.update({
            'director_position': "Директор",
            'director_name': "Иванов Иван Иванович",
            'director_name_initials': "И.И. Иванов",
        })

    return context


def prepare_internship_context(employee, context):
    """
    Подготавливает контекст для руководителя стажировки.
    Args:
        employee: Объект модели Employee
        context: Существующий контекст
    Returns:
        Dict[str, Any]: Обновленный контекст
    """
    from directory.views.documents.utils import get_internship_leader, get_internship_leader_name
    from directory.views.documents.utils import get_internship_leader_position, get_internship_leader_initials
    from directory.utils.declension import decline_phrase, decline_full_name

    leader_position, position_success = get_internship_leader_position(employee)
    leader_name, name_success = get_internship_leader_name(employee)
    leader_initials, initials_success = get_internship_leader_initials(employee)

    internship_leader, level, success = get_internship_leader(employee)

    logger.info(f"Получена информация о руководителе стажировки: success={success}, level={level}, position={leader_position}, name={leader_name}")

    context.update({
        'head_of_internship_position': leader_position,
        'head_of_internship_name': leader_name,
        'head_of_internship_name_initials': leader_initials,
        'head_of_internship_position_genitive': decline_phrase(leader_position, 'gent') if position_success else leader_position,
        'head_of_internship_name_genitive': decline_full_name(leader_name, 'gent') if name_success else leader_name,
        'internship_leader_level': level,
    })

    for key in ['head_of_internship_position_genitive', 'head_of_internship_name_genitive']:
        if not context.get(key):
            logger.warning(f"Отсутствует значение для ключа {key} в контексте распоряжения о стажировке")

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
        try:
            template = DocumentTemplate.objects.get(id=template_id)
            logger.info(f"Шаблон найден: {template.name} (ID: {template_id})")
        except DocumentTemplate.DoesNotExist:
            logger.error(f"Шаблон с ID {template_id} не найден в базе данных")
            raise ValueError(f"Шаблон с ID {template_id} не найден в базе данных")

        template_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))

        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не найден: {template_path}")
            raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")

        file_size = os.path.getsize(template_path)
        if file_size == 0:
            logger.error(f"Файл шаблона пуст: {template_path}")
            raise ValueError(f"Файл шаблона имеет нулевой размер: {template_path}")

        logger.info(f"Файл шаблона готов к обработке: {template_path}, размер: {file_size} байт")

        try:
            doc = DocxTemplate(template_path)
            logger.info("Шаблон успешно загружен в DocxTemplate")
        except Exception as e:
            logger.error(f"Ошибка при загрузке шаблона в DocxTemplate: {str(e)}")
            raise ValueError(f"Ошибка при загрузке шаблона в DocxTemplate: {str(e)}")

        common_keys = ['fio_dative', 'position_dative', 'department', 'subdivision',
                       'head_of_internship_position', 'head_of_internship_name',
                       'head_of_internship_name_initials', 'director_position',
                       'director_name_initials', 'employee_name_initials']
        missing_keys = [key for key in common_keys if key not in context]
        if missing_keys:
            logger.warning(f"В контексте отсутствуют часто используемые ключи: {missing_keys}")

        try:
            doc.render(context)
            logger.info("Шаблон успешно заполнен данными")
        except Exception as e:
            logger.error(f"Ошибка при заполнении шаблона данными: {str(e)}")
            raise ValueError(f"Ошибка при заполнении шаблона данными: {str(e)}")

        filename = f"{template.document_type}_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        logger.info(f"Имя файла для сохранения: {filename}")

        docx_buffer = io.BytesIO()
        doc.save(docx_buffer)
        docx_buffer.seek(0)

        file_content = docx_buffer.getvalue()
        if len(file_content) == 0:
            logger.error(f"Создан пустой DOCX файл для {filename}")
            raise ValueError("Создан пустой DOCX файл")
        else:
            logger.info(f"Создан DOCX файл {filename}, размер: {len(file_content)} байт")

        generated_doc = GeneratedDocument()
        generated_doc.template = template
        generated_doc.employee = employee
        generated_doc.created_by = user

        context.pop('employee', None)
        generated_doc.document_data = context

        try:
            generated_doc.document_file.save(filename, ContentFile(file_content))
            generated_doc.save()
            logger.info(f"Документ успешно сохранен в базу данных с ID: {generated_doc.id}")

            file_path = os.path.join(settings.MEDIA_ROOT, str(generated_doc.document_file))
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                logger.info(f"Проверка после сохранения: файл существует по пути {file_path}, размер: {os.path.getsize(file_path)} байт")
            else:
                logger.warning(f"Проверка после сохранения: файл не найден или пуст по пути {file_path}")

            return generated_doc
        except Exception as e:
            logger.error(f"Ошибка при сохранении документа: {str(e)}")
            raise ValueError(f"Ошибка при сохранении документа: {str(e)}")
    except Exception as e:
        logger.error(f"Ошибка при генерации документа: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def generate_all_orders(employee, user=None, custom_context=None):
    try:
        template = get_document_template('all_orders', employee)
        if not template:
            logger.error("Активный шаблон для комбинированного распоряжения не найден")
            raise ValueError("Активный шаблон для комбинированного распоряжения не найден")

        context = prepare_employee_context(employee)
        logger.info(f"Базовый контекст подготовлен: {list(context.keys())}")

        context = prepare_internship_context(employee, context)
        logger.info("Контекст дополнен информацией о руководителе стажировки")

        now = datetime.datetime.now()
        if not custom_context or 'order_number' not in custom_context:
            context.update({
                'order_number': f"РСТ-{now.strftime('%Y%m%d')}-{employee.id}",
                'order_date': now.strftime("%d.%m.%Y"),
            })

        internship_days = getattr(employee.position, 'internship_period_days', 2) if employee.position else 2
        context['internship_duration'] = internship_days

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        key_variables = ['fio_dative', 'position_dative', 'internship_duration',
                         'head_of_internship_position_genitive', 'head_of_internship_name_genitive']
        for key in key_variables:
            if key not in context or not context[key]:
                logger.warning(f"Отсутствует или пустое значение для ключа {key}")

        logger.info(f"Итоговый контекст для шаблона содержит {len(context)} переменных")
        logger.debug(f"Итоговый контекст для шаблона: {list(context.keys())}")

        result = generate_docx_from_template(template.id, context, employee, user)
        if result:
            logger.info(f"Документ успешно сгенерирован: {result.id}")
            return result
        else:
            logger.error("Ошибка при генерации документа: функция generate_docx_from_template вернула None")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации комбинированного распоряжения: {str(e)}")
        logger.error(traceback.format_exc())
        return None


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
    try:
        template = get_document_template('knowledge_protocol', employee)
        if not template:
            logger.error("Активный шаблон для протокола проверки знаний не найден")
            raise ValueError("Активный шаблон для протокола проверки знаний не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении шаблона протокола проверки знаний: {str(e)}")
        return None

    context = prepare_employee_context(employee)

    now = datetime.datetime.now()
    context.update({
        'protocol_number': f"ПЗ-{now.strftime('%Y%m%d')}-{employee.id}",
        'protocol_date': now.strftime("%d.%m.%Y"),
    })

    # Используем функцию get_commission_formatted для получения данных комиссии
    from directory.views.documents.utils import get_commission_formatted
    commission_data, commission_success = get_commission_formatted(employee)
    context.update({
         'commission_chairman': commission_data.get('chairman', 'Иванов И.И., директор'),
         'commission_members': commission_data.get('members', ['Петров П.П., зам. директора']),
         'commission_secretary': commission_data.get('secretary', 'Кузнецова К.К., секретарь'),
    })

    context['ticket_number'] = context.get('ticket_number', employee.id % 20 + 1)
    context['test_result'] = context.get('test_result', 'прошел')

    if custom_context:
        context.update(custom_context)

    return generate_docx_from_template(template.id, context, employee, user)


def generate_familiarization_document(employee, document_list=None, user=None, custom_context=None):
    try:
        template = get_document_template('doc_familiarization', employee)
        if not template:
            logger.error("Активный шаблон для листа ознакомления не найден")
            raise ValueError("Активный шаблон для листа ознакомления не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении шаблона листа ознакомления: {str(e)}")
        return None

    context = prepare_employee_context(employee)

    if not document_list:
        from directory.views.documents.utils import get_employee_documents
        document_list, success = get_employee_documents(employee)

    context.update({
        'documents_list': document_list,
        'familiarization_date': context['current_date'],
    })

    if custom_context:
        context.update(custom_context)

    return generate_docx_from_template(template.id, context, employee, user)


def generate_siz_card(employee, user=None, custom_context=None):
    try:
        from directory.views.documents.siz_integration import generate_siz_card_excel
        from django.http import HttpRequest

        request = HttpRequest()
        request.user = user

        return generate_siz_card_excel(request, employee.id)
    except Exception as e:
        logger.error(f"Ошибка при генерации карточки СИЗ: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def generate_personal_ot_card(employee, user=None, custom_context=None):
    try:
        template = get_document_template('personal_ot_card', employee)
        if not template:
            logger.error("Шаблон для личной карточки по ОТ не найден")
            raise ValueError("Шаблон для личной карточки по ОТ не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении шаблона личной карточки по ОТ: {str(e)}")
        return None

    context = prepare_employee_context(employee)
    context.update({
        'ot_card_number': f"OT-{employee.id}",
        'card_date': context['current_date'],
    })

    if custom_context:
        context.update(custom_context)

    return generate_docx_from_template(template.id, context, employee, user)


def generate_journal_example(employee, user=None, custom_context=None):
    try:
        template = get_document_template('journal_example', employee)
        if not template:
            logger.error("Шаблон для образца заполнения журнала не найден")
            raise ValueError("Шаблон для образца заполнения журнала не найден")
    except Exception as e:
        logger.error(f"Ошибка при получении шаблона образца заполнения журнала: {str(e)}")
        return None

    context = prepare_employee_context(employee)
    context.update({
        'journal_name': "Журнал регистрации инструктажей по охране труда",
        'journal_sample_date': context['current_date'],
    })

    if custom_context:
        context.update(custom_context)

    return generate_docx_from_template(template.id, context, employee, user)


def analyze_template(template_id):
    """
    Анализ переменных, используемых в шаблоне документа.
    Полезно для отладки проблем с шаблонами.
    Args:
        template_id: ID шаблона для анализа
    """
    import re
    try:
        template = DocumentTemplate.objects.get(id=template_id)
        template_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))

        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не найден: {template_path}")
            return

        from docx import Document
        doc = Document(template_path)
        content = ""
        for para in doc.paragraphs:
            content += para.text + "\n"
        variables = re.findall(r'{{[\s]*([^}]+)[\s]*}}', content)
        logger.info(f"Найденные переменные в шаблоне {template.name}:")
        for var in variables:
            logger.info(f"- {var.strip()}")
    except Exception as e:
        logger.error(f"Ошибка при анализе шаблона: {str(e)}")
