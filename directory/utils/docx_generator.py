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
        'internship_duration': "2",  # Продолжительность стажировки в днях
        # Место нахождения (из организации)
        'location': employee.organization.location if employee.organization and hasattr(employee.organization, 'location') and employee.organization.location else "г. Минск",
        # Поля для отображения в шаблоне
        'employee_name_initials': get_initials_from_name(employee.full_name_nominative),
    }

    # Добавляем поиск подписанта распоряжений
    from directory.views.documents.utils import get_document_signer

    signer, level, found = get_document_signer(employee)
    if found:
        context.update({
            'director_position': signer.position.position_name,
            'director_name': get_initials_from_name(signer.full_name_nominative),
            'director_name_initials': get_initials_from_name(signer.full_name_nominative),
            'director_level': level,  # Может пригодиться для отладки
        })
    else:
        # Значения по умолчанию, если подписант не найден
        context.update({
            'director_position': "Директор",
            'director_name': "И.И. Иванов",
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
    # Импортируем необходимые функции
    from directory.views.documents.utils import get_internship_leader, get_internship_leader_name
    from directory.views.documents.utils import get_internship_leader_position, get_internship_leader_initials
    from directory.utils.declension import decline_phrase, decline_full_name

    # Получаем информацию о руководителе стажировки
    leader_position, position_success = get_internship_leader_position(employee)
    leader_name, name_success = get_internship_leader_name(employee)
    leader_initials, initials_success = get_internship_leader_initials(employee)
    
    # Получаем объект руководителя для отладки
    internship_leader, level, success = get_internship_leader(employee)
    
    logger.info(f"Получена информация о руководителе стажировки: "
               f"success={success}, level={level}, "
               f"position={leader_position}, name={leader_name}")
    
    # Обновляем контекст информацией о руководителе
    context.update({
        'head_of_internship_position': leader_position,
        'head_of_internship_name': leader_name,
        'head_of_internship_name_initials': leader_initials,
        'head_of_internship_position_genitive': decline_phrase(leader_position, 'gent') if position_success else leader_position,
        'head_of_internship_name_genitive': decline_full_name(leader_name, 'gent') if name_success else leader_name,
        'internship_leader_level': level,  # Добавляем для отладки
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
        try:
            template = DocumentTemplate.objects.get(id=template_id)
            logger.info(f"Шаблон найден: {template.name} (ID: {template_id})")
        except DocumentTemplate.DoesNotExist:
            logger.error(f"Шаблон с ID {template_id} не найден в базе данных")
            raise ValueError(f"Шаблон с ID {template_id} не найден в базе данных")

        template_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))

        # Проверяем существование файла шаблона
        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не найден: {template_path}")
            raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")
            
        # Проверяем размер файла
        file_size = os.path.getsize(template_path)
        if file_size == 0:
            logger.error(f"Файл шаблона пуст: {template_path}")
            raise ValueError(f"Файл шаблона имеет нулевой размер: {template_path}")
            
        logger.info(f"Файл шаблона готов к обработке: {template_path}, размер: {file_size} байт")

        # Загружаем шаблон
        try:
            doc = DocxTemplate(template_path)
            logger.info(f"Шаблон успешно загружен в DocxTemplate")
        except Exception as e:
            logger.error(f"Ошибка при загрузке шаблона в DocxTemplate: {str(e)}")
            raise ValueError(f"Ошибка при загрузке шаблона в DocxTemplate: {str(e)}")

        # Проверяем наличие ключевых переменных в контексте
        common_keys = ['fio_dative', 'position_dative', 'department', 'subdivision', 
                      'head_of_internship_position', 'head_of_internship_name', 
                      'head_of_internship_name_initials', 'director_position', 
                      'director_name_initials', 'employee_name_initials']
        
        missing_keys = [key for key in common_keys if key not in context]
        if missing_keys:
            logger.warning(f"В контексте отсутствуют часто используемые ключи: {missing_keys}")

        # Заполняем шаблон контекстом
        try:
            doc.render(context)
            logger.info(f"Шаблон успешно заполнен данными")
        except Exception as e:
            logger.error(f"Ошибка при заполнении шаблона данными: {str(e)}")
            raise ValueError(f"Ошибка при заполнении шаблона данными: {str(e)}")

        # Создаем имя для сгенерированного файла
        filename = f"{template.document_type}_{employee.full_name_nominative.split()[0]}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        logger.info(f"Имя файла для сохранения: {filename}")

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
        try:
            generated_doc.document_file.save(filename, ContentFile(file_content))
            generated_doc.save()
            logger.info(f"Документ успешно сохранен в базу данных с ID: {generated_doc.id}")
            
            # Проверяем файл в файловой системе после сохранения
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
        # Логирование ошибки с полной трассировкой
        logger.error(f"Ошибка при генерации документа: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def get_document_template(document_type):
    """
    Получает шаблон документа определенного типа.
    Args:
        document_type (str): Тип документа ('all_orders', 'knowledge_protocol', etc.)
    Returns:
        DocumentTemplate: Объект шаблона документа или None, если шаблон не найден
    Example:
        template = get_document_template('all_orders')
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


def generate_all_orders(employee, user=None, custom_context=None):
    """
    Генерирует комбинированное распоряжение для сотрудника.
    Включает стажировку и допуск к самостоятельной работе.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        # Пробуем получить шаблон для комбинированного распоряжения
        template = None
        templates = DocumentTemplate.objects.filter(document_type='all_orders', is_active=True).order_by('-updated_at')
        
        if templates.exists():
            template = templates.first()
            logger.info(f"Найден шаблон для комбинированного распоряжения: {template.name} (ID: {template.id})")
        else:
            logger.error("Активный шаблон для комбинированного распоряжения не найден")
            raise ValueError("Активный шаблон для комбинированного распоряжения не найден")
        
        # Проверяем наличие файла шаблона
        template_path = os.path.join(settings.MEDIA_ROOT, str(template.template_file))
        if not os.path.exists(template_path):
            logger.error(f"Файл шаблона не существует по пути: {template_path}")
            raise FileNotFoundError(f"Файл шаблона не найден: {template_path}")
            
        # Проверяем размер файла шаблона
        file_size = os.path.getsize(template_path)
        if file_size == 0:
            logger.error(f"Файл шаблона пуст: {template_path}")
            raise ValueError(f"Файл шаблона имеет нулевой размер: {template_path}")
        
        logger.info(f"Файл шаблона найден: {template_path}, размер: {file_size} байт")

        # Подготавливаем базовый контекст
        context = prepare_employee_context(employee)
        logger.info(f"Базовый контекст подготовлен: {list(context.keys())}")

        # Обновляем контекст информацией о руководителе стажировки
        context = prepare_internship_context(employee, context)
        logger.info(f"Контекст дополнен информацией о руководителе стажировки")

        # Добавляем номера распоряжений если они не указаны в custom_context
        now = datetime.datetime.now()
        if not custom_context or 'order_number' not in custom_context:
            context.update({
                'order_number': f"ОТ-{now.strftime('%Y%m%d')}-{employee.id}",
                'order_date': now.strftime("%d.%m.%Y"),
            })
        
        # Если есть дополнительные данные, добавляем их в контекст
        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")
        
        logger.info(f"Итоговый контекст для шаблона: {list(context.keys())}")
        
        # Генерируем документ
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

    commission_members, commission_success = get_commission_members(employee)
    if commission_success:
        context['commission_members'] = commission_members
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
        document_list, success = get_employee_documents(employee)

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


def generate_siz_card(employee, user=None, custom_context=None):
    """
    Генерирует карточку учета СИЗ для сотрудника.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Переадресуем на существующий механизм генерации карточки СИЗ
    try:
        from directory.views.documents.siz_integration import generate_siz_card_excel
        from django.http import HttpRequest
        
        # Создаем фиктивный объект запроса
        request = HttpRequest()
        request.user = user
        
        # Вызываем функцию генерации карточки СИЗ
        return generate_siz_card_excel(request, employee.id)
    except Exception as e:
        logger.error(f"Ошибка при генерации карточки СИЗ: {str(e)}")
        logger.error(traceback.format_exc())
        return None