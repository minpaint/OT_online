# D:\YandexDisk\OT_online\directory\utils\docx_generator.py
"""
📄 Модуль для генерации документов Word

Этот модуль содержит функции для работы с шаблонами DOCX и
генерации документов на основе данных из системы.
"""
import os
import uuid
from typing import Dict, Any, Optional, Tuple, List
import datetime
from docxtpl import DocxTemplate
from django.conf import settings
from django.core.files.base import ContentFile

from directory.models.document_template import DocumentTemplate, GeneratedDocument
from directory.utils.declension import decline_full_name, decline_phrase, get_initials_from_name


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
    Также проверяет наличие необходимых данных и формирует список недостающих.

    Args:
        employee: Объект модели Employee
    Returns:
        Dict[str, Any]: Словарь с данными для заполнения шаблона и информацией о недостающих данных
    """
    # Получаем текущую дату в разных форматах
    now = datetime.datetime.now()
    date_str = now.strftime("%d.%m.%Y")
    day = now.strftime("%d")
    month = now.strftime("%m")
    year = now.strftime("%Y")
    year_short = now.strftime("%y")

    # Список для хранения недостающих данных
    missing_data = []

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
    }

    # Проверяем наличие должности
    if not employee.position:
        missing_data.append("Должность сотрудника")
    else:
        # Должность в разных падежах
        context.update({
            'position_nominative': employee.position.position_name,
            'position_genitive': decline_phrase(employee.position.position_name, 'gent'),
            'position_dative': decline_phrase(employee.position.position_name, 'datv'),
            'position_accusative': decline_phrase(employee.position.position_name, 'accs'),
            'position_instrumental': decline_phrase(employee.position.position_name, 'ablt'),
            'position_prepositional': decline_phrase(employee.position.position_name, 'loct'),
        })

    # Проверяем наличие отдела и подразделения
    if employee.department:
        context.update({
            'department': employee.department.name,
            'department_genitive': decline_phrase(employee.department.name, 'gent'),
            'department_dative': decline_phrase(employee.department.name, 'datv'),
        })
    elif employee.subdivision:  # Есть подразделение, но нет отдела
        context['department'] = ""
        context['department_genitive'] = ""
        context['department_dative'] = ""
    else:  # Нет ни отдела, ни подразделения
        missing_data.append("Отдел или подразделение")
        context['department'] = ""
        context['department_genitive'] = ""
        context['department_dative'] = ""

    # Проверяем наличие подразделения
    if employee.subdivision:
        context.update({
            'subdivision': employee.subdivision.name,
            'subdivision_genitive': decline_phrase(employee.subdivision.name, 'gent'),
            'subdivision_dative': decline_phrase(employee.subdivision.name, 'datv'),
        })
    else:
        context['subdivision'] = ""
        context['subdivision_genitive'] = ""
        context['subdivision_dative'] = ""

    # Проверяем наличие организации
    if not employee.organization:
        missing_data.append("Организация")
        context['organization_name'] = ""
        context['organization_full_name'] = ""
    else:
        context.update({
            'organization_name': employee.organization.short_name_ru,
            'organization_full_name': employee.organization.full_name_ru,
        })

    # Даты и номера документов
    context.update({
        'current_date': date_str,
        'current_day': day,
        'current_month': month,
        'current_year': year,
        'current_year_short': year_short,
        'order_date': date_str,
        # Поля для номеров документов - заполняются отдельно
        'order_number': "",
        # Дополнительные поля
        'internship_duration': "2",  # Продолжительность стажировки в днях
    })

    # Место нахождения (из организации)
    if employee.organization and hasattr(employee.organization, 'location') and employee.organization.location:
        context['location'] = employee.organization.location
    else:
        context['location'] = "г. Минск"
        missing_data.append("Место нахождения организации")

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
        # Отмечаем как недостающие данные
        missing_data.append("Подписант документа")
        context.update({
            'director_position': "",
            'director_name': "",
        })

    # Добавляем информацию о недостающих данных в контекст
    context['missing_data'] = missing_data
    context['has_missing_data'] = len(missing_data) > 0

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

        # Загружаем шаблон
        doc = DocxTemplate(template_path)

        # Удаляем служебные ключи из контекста перед заполнением шаблона
        clean_context = {k: v for k, v in context.items() if k not in ['missing_data', 'has_missing_data']}

        # Заполняем шаблон контекстом
        doc.render(clean_context)

        # Создаем имя для сгенерированного файла
        filename = f"{template.document_type}_{employee.full_name_nominative}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"

        # Сохраняем в память
        file_content = ContentFile(b'')
        doc.save(file_content)

        # Создаем запись о сгенерированном документе
        generated_doc = GeneratedDocument()
        generated_doc.template = template
        generated_doc.employee = employee
        generated_doc.created_by = user
        generated_doc.document_data = context
        generated_doc.document_file.save(filename, file_content)
        generated_doc.save()

        return generated_doc

    except Exception as e:
        # Логирование ошибки
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Ошибка при генерации документа: {str(e)}")
        return None


def generate_all_orders(employee, user=None, custom_context=None):
    """
    Генерирует все распоряжения для сотрудника (заменяет отдельные функции для каждого типа распоряжения).
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
    # Получаем шаблон для распоряжений о стажировке
    try:
        template = DocumentTemplate.objects.get(document_type='all_orders', is_active=True)
    except DocumentTemplate.DoesNotExist:
        raise ValueError("Активный шаблон для распоряжений о стажировке не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Ищем руководителя стажировки с иерархическим подходом
    from directory.views.documents.utils import get_internship_leader

    internship_leader, level, success = get_internship_leader(employee)
    if success and internship_leader:
        context.update({
            'head_of_internship_name': internship_leader.full_name_nominative,
            'head_of_internship_name_initials': get_initials_from_name(internship_leader.full_name_nominative),
            'head_of_internship_position': internship_leader.position.position_name if internship_leader.position else "",
            'internship_leader_level': level,  # Добавляем для отладки
        })
    else:
        # Отмечаем как недостающие данные
        context['missing_data'].append("Руководитель стажировки")

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        # Проверяем наличие ключа missing_data в пользовательском контексте
        if 'missing_data' in custom_context:
            custom_missing_data = custom_context.pop('missing_data')
            # Объединяем списки недостающих данных
            context['missing_data'].extend(custom_missing_data)
            # Обновляем флаг наличия недостающих данных
            context['has_missing_data'] = len(context['missing_data']) > 0

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
    # Получаем шаблон для карточки учета СИЗ
    try:
        template = DocumentTemplate.objects.get(document_type='siz_card', is_active=True)
    except DocumentTemplate.DoesNotExist:
        raise ValueError("Активный шаблон для карточки учета СИЗ не найден")

    # Подготавливаем базовый контекст
    context = prepare_employee_context(employee)

    # Получаем данные из карточки учета СИЗ
    from directory.models import SIZNorm, SIZIssued

    # Получаем базовые нормы СИЗ для должности
    if employee.position:
        base_norms = SIZNorm.objects.filter(position=employee.position, condition='').select_related('siz')
        context['base_norms'] = list(base_norms)

        # Получаем условные нормы СИЗ
        condition_norms = SIZNorm.objects.filter(position=employee.position).exclude(condition='').select_related('siz')
        condition_groups = {}
        for norm in condition_norms:
            if norm.condition not in condition_groups:
                condition_groups[norm.condition] = []
            condition_groups[norm.condition].append(norm)

        context['condition_groups'] = [{'name': name, 'norms': norms} for name, norms in condition_groups.items()]
    else:
        context['missing_data'].append("Нормы выдачи СИЗ")
        context['base_norms'] = []
        context['condition_groups'] = []

    # Получаем выданные СИЗ
    issued_items = SIZIssued.objects.filter(employee=employee).select_related('siz').order_by('-issue_date')
    context['issued_items'] = list(issued_items)

    # Определяем пол сотрудника по ФИО для правильного заполнения карточки
    from directory.utils.declension import get_gender_from_name
    gender = get_gender_from_name(employee.full_name_nominative)
    context['gender'] = "Мужской" if gender == 'masc' else "Женский"

    # Получаем размеры СИЗ для сотрудника
    context['siz_sizes'] = {
        'headgear': "",  # Размер головного убора
        'respirator': "", # Размер СИЗОД
        'gloves': employee.clothing_size if hasattr(employee, 'clothing_size') else "",  # Размер перчаток/рукавиц
    }

    # Если есть пользовательский контекст, обновляем основной контекст
    if custom_context:
        # Проверяем наличие ключа missing_data в пользовательском контексте
        if 'missing_data' in custom_context:
            custom_missing_data = custom_context.pop('missing_data')
            # Объединяем списки недостающих данных
            context['missing_data'].extend(custom_missing_data)
            # Обновляем флаг наличия недостающих данных
            context['has_missing_data'] = len(context['missing_data']) > 0

        context.update(custom_context)

    # Генерируем документ
    return generate_docx_from_template(template.id, context, employee, user)


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
        import logging
        logger = logging.getLogger(__name__)
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
        return None

    # Подготавливаем базовый контекст
    base_context = prepare_employee_context(employee)

    # Если есть дополнительный контекст, обновляем основной контекст
    if context:
        # Проверяем наличие ключа missing_data в пользовательском контексте
        if 'missing_data' in context:
            custom_missing_data = context.pop('missing_data')
            # Объединяем списки недостающих данных
            base_context['missing_data'].extend(custom_missing_data)
            # Обновляем флаг наличия недостающих данных
            base_context['has_missing_data'] = len(base_context['missing_data']) > 0

        base_context.update(context)

    # Генерируем документ
    return generate_docx_from_template(template.id, base_context, employee, user)