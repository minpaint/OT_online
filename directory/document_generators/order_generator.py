# directory/document_generators/order_generator.py
"""
📄 Генератор для комбинированного распоряжения (Прием/Стажировка)
"""
import logging
import datetime
import traceback
from typing import Dict, Any, Optional

from directory.models.document_template import GeneratedDocument
from directory.document_generators.base import (
    get_document_template, prepare_employee_context, generate_docx_from_template
)
from directory.utils.declension import decline_phrase, decline_full_name, get_initials_from_name

# Настройка логирования
logger = logging.getLogger(__name__)

def prepare_internship_context(employee, context):
    """
    Подготавливает контекст для руководителя стажировки.
    Args:
        employee: Объект модели Employee
        context: Существующий контекст
    Returns:
        Dict[str, Any]: Обновленный контекст
    """
    # Импорты перенесены сюда, чтобы избежать циклической зависимости
    from directory.views.documents.utils import (
        get_internship_leader, get_internship_leader_name,
        get_internship_leader_position, get_internship_leader_initials
    )

    leader_position, position_success = get_internship_leader_position(employee)
    leader_name, name_success = get_internship_leader_name(employee)
    leader_initials, initials_success = get_internship_leader_initials(employee)

    internship_leader, level, success = get_internship_leader(employee)

    logger.info(f"Получена информация о руководителе стажировки: success={success}, level={level}, position={leader_position}, name={leader_name}")
    logger.debug(f"Объект руководителя стажировки: {internship_leader}") # Лог объекта

    # Получение и склонение отдела и подразделения руководителя
    head_dept_genitive = ""
    head_subdiv_genitive = ""
    if internship_leader and success: # Проверяем, что объект руководителя найден
        logger.info(f"Руководитель стажировки найден: {internship_leader.full_name_nominative if internship_leader else 'Нет данных'}")
        if hasattr(internship_leader, 'department') and internship_leader.department:
            dept_name = internship_leader.department.name
            logger.info(f"Найден отдел руководителя: '{dept_name}'")
            try:
                head_dept_genitive = decline_phrase(dept_name, 'gent')
                logger.info(f"Результат склонения отдела ('{dept_name}' -> 'gent'): '{head_dept_genitive}'")
            except Exception as e:
                logger.warning(f"Не удалось просклонять отдел руководителя стажировки: {dept_name}, ошибка: {e}")
                head_dept_genitive = dept_name # Запасной вариант - исходное название
        else:
             logger.warning(f"У руководителя стажировки {internship_leader} не указан отдел или отсутствует атрибут 'department'.")

        if hasattr(internship_leader, 'subdivision') and internship_leader.subdivision:
            subdiv_name = internship_leader.subdivision.name
            logger.info(f"Найдено подразделение руководителя: '{subdiv_name}'")
            try:
                head_subdiv_genitive = decline_phrase(subdiv_name, 'gent')
                logger.info(f"Результат склонения подразделения ('{subdiv_name}' -> 'gent'): '{head_subdiv_genitive}'")
            except Exception as e:
                logger.warning(f"Не удалось просклонять подразделение руководителя стажировки: {subdiv_name}, ошибка: {e}")
                head_subdiv_genitive = subdiv_name # Запасной вариант - исходное название
        else:
            logger.warning(f"У руководителя стажировки {internship_leader} не указано подразделение или отсутствует атрибут 'subdivision'.")
    else:
        logger.warning("Не удалось получить объект руководителя стажировки или success=False для определения отдела/подразделения.")


    context.update({
        'head_of_internship_position': leader_position,
        'head_of_internship_name': leader_name,
        'head_of_internship_name_initials': leader_initials,
        'head_of_internship_position_genitive': decline_phrase(leader_position, 'gent') if position_success else leader_position, # Оставляем для совместимости
        'head_of_internship_name_accusative': decline_full_name(leader_name, 'accs') if name_success else leader_name,
        'head_of_internship_position_accusative': decline_phrase(leader_position, 'accs') if position_success else leader_position, # Добавлено
        'internship_leader_level': level,
        # >>> Новые добавленные ключи <<<
        'head_of_internship_department_genitive': head_dept_genitive,
        'head_of_internship_subdivision_genitive': head_subdiv_genitive,
    })

    logger.debug(f"Обновленный контекст для руководителя стажировки: department_genitive='{head_dept_genitive}', subdivision_genitive='{head_subdiv_genitive}'")

    # Проверяем наличие accusative
    for key in ['head_of_internship_name_accusative', 'head_of_internship_position_accusative']:
        if not context.get(key):
            logger.warning(f"Отсутствует значение для ключа {key} в контексте распоряжения о стажировке")

    return context

# Остальная часть файла generate_all_orders без изменений...
def generate_all_orders(employee, user=None, custom_context: Optional[Dict[str, Any]] = None) -> Optional[GeneratedDocument]:
    """
    Генерирует комбинированное распоряжение о приеме/стажировке.
    Args:
        employee: Объект модели Employee
        user: Пользователь, создающий документ (опционально)
        custom_context: Пользовательский контекст (опционально)
    Returns:
        Optional[GeneratedDocument]: Объект сгенерированного документа или None при ошибке
    """
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
        # Добавляем номер и дату распоряжения по умолчанию, если они не переданы
        if not custom_context or 'order_number' not in custom_context:
            context.setdefault('order_number', f"РСТ-{now.strftime('%Y%m%d')}-{employee.id}")
        if not custom_context or 'order_date' not in custom_context:
            context.setdefault('order_date', now.strftime("%d.%m.%Y"))

        internship_days = getattr(employee.position, 'internship_period_days', 2) if employee.position else 2
        context['internship_duration'] = internship_days

        if custom_context:
            context.update(custom_context)
            logger.info(f"Контекст дополнен пользовательскими данными: {list(custom_context.keys())}")

        # Проверка ключевых переменных (можно добавить больше при необходимости)
        # Обновил проверку, чтобы использовать accusative падеж
        key_variables = ['fio_dative', 'position_dative', 'internship_duration',
                         'head_of_internship_position_accusative', 'head_of_internship_name_accusative']
        # Добавляем проверку на новые переменные (опционально, т.к. могут быть пустыми)
        # key_variables.extend(['head_of_internship_department_genitive', 'head_of_internship_subdivision_genitive'])

        for key in key_variables:
            if key not in context or not context[key]:
                # Если это новые ключи и они пустые - это нормально, не выдаем warning
                if key not in ['head_of_internship_department_genitive', 'head_of_internship_subdivision_genitive']:
                    logger.warning(f"Отсутствует или пустое значение для ключевой переменной '{key}'")

        logger.info(f"Итоговый контекст для шаблона содержит {len(context)} переменных")
        logger.debug(f"Итоговый контекст для шаблона (ключи): {list(context.keys())}") # Лог ключей итогового контекста

        # Вызываем базовую функцию генерации
        result = generate_docx_from_template(template, context, employee, user)
        if result:
            logger.info(f"Документ 'all_orders' успешно сгенерирован: {result.id}")
            return result
        else:
            logger.error("Ошибка при генерации документа: функция generate_docx_from_template вернула None")
            return None
    except Exception as e:
        logger.error(f"Ошибка при генерации комбинированного распоряжения: {str(e)}")
        logger.error(traceback.format_exc())
        return None
