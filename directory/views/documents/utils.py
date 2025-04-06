"""
🔧 Вспомогательные функции для работы с документами

Содержит утилиты и вспомогательные функции для работы с документами.
"""
import logging
from directory.utils.declension import get_initials_from_name, decline_full_name, decline_phrase
from directory.models import Employee

# Настройка логирования
logger = logging.getLogger(__name__)


def get_internship_leader(employee):
    """
    Выполняет иерархический поиск руководителя стажировки для сотрудника
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (leader, level, success)
        где level: "department", "subdivision", "organization"
    """
    # 1. Сначала ищем в отделе
    if employee.department:
        leader = employee.department.employees.filter(
            position__can_be_internship_leader=True
        ).first()
        if leader:
            return leader, "department", True

    # 2. Если не нашли, ищем в подразделении
    if employee.subdivision:
        # Используем прямой запрос к модели Employee
        leader = Employee.objects.filter(
            subdivision=employee.subdivision,
            position__can_be_internship_leader=True,
            department__isnull=True  # Сотрудники напрямую в подразделении
        ).first()
        if leader:
            return leader, "subdivision", True

    # 3. Если не нашли, ищем в организации
    if employee.organization:
        # Используем прямой запрос к модели Employee
        leader = Employee.objects.filter(
            organization=employee.organization,
            position__can_be_internship_leader=True,
            subdivision__isnull=True,  # Сотрудники напрямую в организации
            department__isnull=True
        ).first()
        if leader:
            return leader, "organization", True

    # Если нигде не нашли
    return None, None, False


def get_document_signer(employee):
    """
    Получает подписанта документов для сотрудника с учетом иерархии
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (signer, level, success)
        где level: "department", "subdivision", "organization"
    """
    # 1. Сначала ищем в отделе
    if employee.department:
        signer = employee.department.employees.filter(
            position__can_sign_orders=True
        ).first()
        if signer:
            return signer, "department", True

    # 2. Если не нашли, ищем в подразделении
    if employee.subdivision:
        # Используем прямой запрос к модели Employee
        signer = Employee.objects.filter(
            subdivision=employee.subdivision,
            position__can_sign_orders=True,
            department__isnull=True  # Сотрудники напрямую в подразделении
        ).first()
        if signer:
            return signer, "subdivision", True

    # 3. Если не нашли, ищем в организации
    if employee.organization:
        # Используем прямой запрос к модели Employee
        signer = Employee.objects.filter(
            organization=employee.organization,
            position__can_sign_orders=True,
            subdivision__isnull=True,  # Сотрудники напрямую в организации
            department__isnull=True
        ).first()
        if signer:
            return signer, "organization", True

    # Если нигде не нашли
    return None, None, False


def get_internship_leader_position(employee):
    """
    Получает должность руководителя стажировки для сотрудника
    Должность возвращается с маленькой буквы.

    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (position_name, success)
    """
    leader, _, success = get_internship_leader(employee)
    if success and leader and leader.position:
        # Преобразуем должность к нижнему регистру (первая буква)
        position_name = leader.position.position_name
        if position_name:
            position_name = position_name[0].lower() + position_name[1:]
        return position_name, True

    return "необходимо указать должность руководителя стажировки", False


def get_internship_leader_name(employee):
    """
    Получает ФИО руководителя стажировки для сотрудника
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (name, success)
    """
    leader, _, success = get_internship_leader(employee)
    if success and leader:
        return leader.full_name_nominative, True

    return "Необходимо указать ФИО руководителя стажировки", False


def get_internship_leader_initials(employee):
    """
    Получает инициалы руководителя стажировки для сотрудника
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (initials, success)
    """
    leader, _, success = get_internship_leader(employee)
    if success and leader:
        return get_initials_from_name(leader.full_name_nominative), True

    return "Необходимо указать инициалы руководителя стажировки", False


def get_director_info(organization):
    """
    Получает информацию о директоре организации
    Args:
        organization: Объект организации Organization
    Returns:
        tuple: ({'position': position, 'name': name}, success)
    """
    # Здесь должна быть реальная логика получения информации о директоре из организации
    # В реальной системе эта информация должна храниться в модели организации

    # Проверка наличия информации о директоре в организации
    if organization and hasattr(organization, 'director_name') and organization.director_name:
        return {
            'position': getattr(organization, 'director_position', 'Директор'),
            'name': organization.director_name
        }, True

    # Не найдено
    return {
        'position': "Директор",
        'name': "И.И. Коржов"  # Значение по умолчанию
    }, False


def get_commission_members(employee):
    """
    Получает список членов комиссии для протокола проверки знаний
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (members_list, success)
    """
    # Проверяем наличие информации о комиссии
    if hasattr(employee.organization, 'commission_members'):
        commission = getattr(employee.organization, 'commission_members', None)
        if commission and len(commission) > 0:
            return commission, True

    # Не найдено - возвращаем шаблон, который пользователь должен заполнить
    return [
        {"role": "Председатель комиссии", "name": "Необходимо указать"},
        {"role": "Член комиссии", "name": "Необходимо указать"},
        {"role": "Член комиссии", "name": "Необходимо указать"},
    ], False


def get_safety_instructions(employee):
    """
    Получает список инструкций по охране труда для сотрудника
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (instructions_list, success)
    """
    # Если у сотрудника есть должность с указанными инструкциями
    if employee.position and hasattr(employee.position, 'safety_instructions_numbers'):
        instructions = employee.position.safety_instructions_numbers
        if instructions:
            # Разбиваем строку с номерами инструкций на список
            instructions_list = [instr.strip() for instr in instructions.split(',')]
            return instructions_list, True

    # Не найдено
    return ["Необходимо указать инструкции"], False


def get_employee_documents(employee):
    """
    Получает список документов, с которыми должен ознакомиться сотрудник
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (documents_list, success)
    """
    # Если у сотрудника есть должность с привязанными документами
    if employee.position and hasattr(employee.position, 'documents'):
        documents = employee.position.documents.all()
        if documents.exists():
            documents_list = [doc.name for doc in documents]
            return documents_list, True

    # Не найдено
    return ["Необходимо указать список документов"], False


def prepare_internship_context(employee, context=None):
    """
    Подготавливает контекст для распоряжения о стажировке,
    включая склонение имени и должности руководителя стажировки
    в родительный падеж.

    Args:
        employee: Объект сотрудника Employee
        context: Существующий контекст (опционально)

    Returns:
        dict: Обновленный контекст с добавленными данными о стажировке
    """
    if context is None:
        context = {}

    # Получаем информацию о руководителе стажировки
    leader, level, success = get_internship_leader(employee)

    if success and leader:
        # Получаем должность и имя в именительном падеже
        leader_position = leader.position.position_name
        leader_name = leader.full_name_nominative

        # Преобразуем первую букву должности в нижний регистр
        if leader_position:
            leader_position = leader_position[0].lower() + leader_position[1:]

        # Получаем инициалы
        leader_name_initials = get_initials_from_name(leader_name)

        # Склоняем в родительный падеж
        leader_position_genitive = decline_phrase(leader_position, 'gent')
        leader_name_genitive = decline_full_name(leader_name, 'gent')

        # Добавляем в контекст оригинальные и склоненные варианты
        context.update({
            'head_of_internship_position': leader_position,
            'head_of_internship_name': leader_name,
            'head_of_internship_name_initials': leader_name_initials,  # Добавляем инициалы
            'head_of_internship_position_genitive': leader_position_genitive,
            'head_of_internship_name_genitive': leader_name_genitive,
            'internship_leader_level': level,  # Для отладки
        })
    else:
        # Добавляем заглушки, если руководитель не найден
        context.update({
            'head_of_internship_position': "необходимо указать должность",
            'head_of_internship_name': "Необходимо указать ФИО",
            'head_of_internship_name_initials': "Н.У.Ф.",  # Заглушка для инициалов
            'head_of_internship_position_genitive': "необходимо указать должность",
            'head_of_internship_name_genitive': "Необходимо указать ФИО",
            'internship_leader_level': None,
        })

    return context


def prepare_director_context(employee, context=None):
    """
    Подготавливает контекст для подписанта документа (директора),
    включая склонение имени и должности в родительный падеж.

    Args:
        employee: Объект сотрудника Employee
        context: Существующий контекст (опционально)

    Returns:
        dict: Обновленный контекст с добавленными данными о подписанте
    """
    if context is None:
        context = {}

    # Получаем информацию о подписанте
    signer, level, success = get_document_signer(employee)

    if success and signer:
        # Получаем должность и имя
        signer_position = signer.position.position_name
        signer_name = signer.full_name_nominative

        # Получаем инициалы
        signer_name_initials = get_initials_from_name(signer_name)

        # Склоняем в родительный падеж
        signer_position_genitive = decline_phrase(signer_position, 'gent')
        signer_name_genitive = decline_full_name(signer_name, 'gent')

        context.update({
            'director_position': signer_position,
            'director_name': signer_name,
            'director_name_initials': signer_name_initials,
            'director_position_genitive': signer_position_genitive,
            'director_name_genitive': signer_name_genitive,
            'director_level': level,  # Для отладки
        })
    else:
        # Если подписант не найден, получаем информацию о директоре организации
        director_info, _ = get_director_info(employee.organization)
        director_position = director_info['position']
        director_name = director_info['name']

        # Склоняем в родительный падеж
        director_position_genitive = decline_phrase(director_position, 'gent')

        # Имя директора может быть уже в формате инициалов (И.И. Иванов)
        # Проверяем формат и обрабатываем соответственно
        if '.' in director_name:
            # Уже в формате инициалов, используем как есть
            director_name_initials = director_name
            director_name_genitive = director_name  # Предполагаем, что уже склонено правильно
        else:
            # Полное имя, генерируем инициалы и склоняем
            director_name_initials = get_initials_from_name(director_name)
            director_name_genitive = decline_full_name(director_name, 'gent')

        context.update({
            'director_position': director_position,
            'director_name': director_name,
            'director_name_initials': director_name_initials,
            'director_position_genitive': director_position_genitive,
            'director_name_genitive': director_name_genitive,
            'director_level': None,
        })

    return context


def get_commission_formatted(employee):
    """
    Получает данные о комиссии в формате, подходящем для шаблонов документов.
    Args:
        employee: Объект модели Employee
    Returns:
        tuple: (данные о комиссии в структурированном формате, успешность выполнения)
    """
    commission_members, success = get_commission_members(employee)
    if not success or not commission_members:
        logger.warning(f"Не удалось получить данные о комиссии для сотрудника {employee.full_name_nominative}")
        return {
            'chairman': 'Иванов И.И., директор',
            'members': ['Петров П.П., зам. директора', 'Сидоров С.С., инженер по ОТ'],
            'secretary': 'Кузнецова К.К., секретарь'
        }, False

    try:
        # Формируем структурированный формат
        result = {
            'chairman': commission_members[0]['name'] if isinstance(commission_members[0], dict) else
            commission_members[0],
            'members': [],
            'secretary': commission_members[-1]['name'] if isinstance(commission_members[-1], dict) else
            commission_members[-1]
        }

        # Если есть промежуточные члены комиссии
        if len(commission_members) > 2:
            for member in commission_members[1:-1]:
                result['members'].append(member['name'] if isinstance(member, dict) else member)
        else:
            result['members'] = ['Петров П.П., зам. директора']

        return result, True
    except Exception as e:
        logger.error(f"Ошибка при форматировании данных комиссии: {str(e)}")
        return {
            'chairman': 'Иванов И.И., директор',
            'members': ['Петров П.П., зам. директора'],
            'secretary': 'Кузнецова К.К., секретарь'
        }, False