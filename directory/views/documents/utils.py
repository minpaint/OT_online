"""
🔧 Вспомогательные функции для работы с документами

Содержит утилиты и вспомогательные функции для работы с документами.
"""
from directory.utils.declension import get_initials_from_name
from directory.models import Employee


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
    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (position_name, success)
    """
    leader, _, success = get_internship_leader(employee)
    if success and leader and leader.position:
        return leader.position.position_name, True

    return "Необходимо указать должность руководителя стажировки", False


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