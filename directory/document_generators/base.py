# directory/document_generators/base.py
"""
📄 Базовый модуль для генерации документов

Содержит общие функции для работы с шаблонами и контекстом.
"""
import os
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


def get_document_template(document_type, employee=None) -> Optional[DocumentTemplate]:
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
        'employee': employee, # Добавляем объект сотрудника в контекст для возможного использования
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
        'organization_name': employee.organization.short_name_ru if employee.organization else "",  # Оставляем именительный падеж
        'organization_name_genitive': decline_phrase(employee.organization.short_name_ru, 'gent') if employee.organization else "",
        'organization_name_dative': decline_phrase(employee.organization.short_name_ru, 'datv') if employee.organization else "",
        'organization_name_accusative': decline_phrase(employee.organization.short_name_ru, 'accs') if employee.organization else "",
        'organization_name_instrumental': decline_phrase(employee.organization.short_name_ru, 'ablt') if employee.organization else "",
        'organization_name_prepositional': decline_phrase(employee.organization.short_name_ru, 'loct') if employee.organization else "",

        'organization_full_name': employee.organization.full_name_ru if employee.organization else "",  # Оставляем именительный падеж
        'organization_full_name_genitive': decline_phrase(employee.organization.full_name_ru, 'gent') if employee.organization else "",
        'organization_full_name_dative': decline_phrase(employee.organization.full_name_ru, 'datv') if employee.organization else "",
        'organization_full_name_accusative': decline_phrase(employee.organization.full_name_ru, 'accs') if employee.organization else "",
        'organization_full_name_instrumental': decline_phrase(employee.organization.full_name_ru, 'ablt') if employee.organization else "",
        'organization_full_name_prepositional': decline_phrase(employee.organization.full_name_ru, 'loct') if employee.organization else "",

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
    # TODO: Переместить эту логику во views или специфичный генератор, если нужно
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

def generate_docx_from_template(template: DocumentTemplate, context: Dict[str, Any],
                                employee, user=None) -> Optional[GeneratedDocument]:
    """
    Генерирует документ DOCX на основе шаблона и контекста данных.
    Args:
        template (DocumentTemplate): Объект шаблона документа
        context (Dict[str, Any]): Словарь с данными для заполнения шаблона
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    try:
        template_path = template.template_file.path
        logger.info(f"Используется шаблон: {template.name} (ID: {template.id}), путь: {template_path}")

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

        # Проверка ключей больше не обязательна здесь, но можно оставить для отладки
        # common_keys = [...] # Список ключей
        # missing_keys = [key for key in common_keys if key not in context]
        # if missing_keys:
        #     logger.warning(f"В контексте отсутствуют часто используемые ключи: {missing_keys}")

        try:
            # Удаляем объект employee из контекста перед рендерингом, чтобы избежать проблем с сериализацией
            context_to_render = context.copy()
            context_to_render.pop('employee', None)
            doc.render(context_to_render)
            logger.info("Шаблон успешно заполнен данными")
        except Exception as e:
            logger.error(f"Ошибка при заполнении шаблона данными: {str(e)}")
            logger.error(f"Контекст при ошибке: {context_to_render.keys()}") # Лог ключей контекста
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

        # Сохраняем контекст без объекта employee
        generated_doc.document_data = context_to_render

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
