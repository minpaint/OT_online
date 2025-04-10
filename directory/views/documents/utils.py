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
    Выполняет иерархический поиск руководителя стажировки для сотрудника.
    Ищет только сотрудников с явно установленным флагом can_be_internship_leader=True.

    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (leader, level, success)
        где level: "department", "subdivision", "organization"
    """
    logger.info(f"Поиск руководителя стажировки для сотрудника {employee.full_name_nominative}")

    # Проверяем, что у сотрудника указана должность
    if not employee.position:
        logger.warning(f"У сотрудника {employee.full_name_nominative} не указана должность")
        return None, None, False

    # Логируем информацию о подразделении и отделе
    logger.info(f"Подразделение: {employee.subdivision.name if employee.subdivision else 'Не указано'}")
    logger.info(f"Отдел: {employee.department.name if employee.department else 'Не указан'}")

    # 1. Сначала ищем в отделе
    if employee.department:
        leaders_in_dept = list(employee.department.employees.filter(
            position__can_be_internship_leader=True
        ).exclude(id=employee.id))  # Исключаем самого сотрудника

        logger.info(f"Найдено {len(leaders_in_dept)} руководителей стажировки в отделе")

        if leaders_in_dept:
            leader = leaders_in_dept[0]
            logger.info(f"Найден руководитель стажировки в отделе: {leader.full_name_nominative}")
            return leader, "department", True

    # 2. Если не нашли, ищем в подразделении
    if employee.subdivision:
        leaders_in_subdiv = list(Employee.objects.filter(
            subdivision=employee.subdivision,
            position__can_be_internship_leader=True,
        ).exclude(id=employee.id))  # Исключаем самого сотрудника

        logger.info(f"Найдено {len(leaders_in_subdiv)} руководителей стажировки в подразделении")

        if leaders_in_subdiv:
            leader = leaders_in_subdiv[0]
            logger.info(f"Найден руководитель стажировки в подразделении: {leader.full_name_nominative}")
            return leader, "subdivision", True

    # 3. Если не нашли, ищем в организации
    if employee.organization:
        leaders_in_org = list(Employee.objects.filter(
            organization=employee.organization,
            position__can_be_internship_leader=True,
        ).exclude(id=employee.id))  # Исключаем самого сотрудника

        logger.info(f"Найдено {len(leaders_in_org)} руководителей стажировки в организации")

        if leaders_in_org:
            leader = leaders_in_org[0]
            logger.info(f"Найден руководитель стажировки в организации: {leader.full_name_nominative}")
            return leader, "organization", True

    # Если нигде не нашли - возвращаем отрицательный результат
    logger.warning(f"Руководитель стажировки для {employee.full_name_nominative} не найден")
    return None, None, False


def get_document_signer(employee):
    """
    Получает подписанта документов для сотрудника с учетом иерархии.
    Ищет только сотрудников с явно установленным флагом can_sign_orders=True.

    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (signer, level, success)
        где level: "department", "subdivision", "organization"
    """
    logger.info(f"Поиск подписанта документов для сотрудника {employee.full_name_nominative}")

    # 1. Сначала ищем в отделе
    if employee.department:
        signer = employee.department.employees.filter(
            position__can_sign_orders=True
        ).first()
        if signer:
            logger.info(f"Найден подписант в отделе: {signer.full_name_nominative}")
            return signer, "department", True

    # 2. Если не нашли, ищем в подразделении
    if employee.subdivision:
        signer = Employee.objects.filter(
            subdivision=employee.subdivision,
            position__can_sign_orders=True,
        ).first()
        if signer:
            logger.info(f"Найден подписант в подразделении: {signer.full_name_nominative}")
            return signer, "subdivision", True

    # 3. Если не нашли, ищем в организации
    if employee.organization:
        signer = Employee.objects.filter(
            organization=employee.organization,
            position__can_sign_orders=True,
        ).first()
        if signer:
            logger.info(f"Найден подписант в организации: {signer.full_name_nominative}")
            return signer, "organization", True

    # Если нигде не нашли
    logger.warning(f"Подписант документов для {employee.full_name_nominative} не найден")
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

    return None, False


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

    return None, False


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

    return None, False


def get_commission_members(employee):
    """
    Получает список членов комиссии для протокола проверки знаний.
    Ищет только сотрудников с явно установленными ролями в комиссии.

    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (members_list, success)
    """
    # Поиск сотрудников по ролям в комиссии
    if employee.organization:
        try:
            # Поиск председателя комиссии
            chairman = Employee.objects.filter(
                organization=employee.organization,
                position__commission_role='chairman'
            ).first()

            # Поиск членов комиссии
            members = list(Employee.objects.filter(
                organization=employee.organization,
                position__commission_role='member'
            ))

            # Поиск секретаря комиссии
            secretary = Employee.objects.filter(
                organization=employee.organization,
                position__commission_role='secretary'
            ).first()

            # Формируем комиссию, если найдены все необходимые участники
            if chairman and members and secretary:
                commission = []

                commission.append({
                    "role": "Председатель комиссии",
                    "name": chairman.full_name_nominative,
                    "position": chairman.position.position_name if chairman.position else "директор"
                })

                for member in members:
                    commission.append({
                        "role": "Член комиссии",
                        "name": member.full_name_nominative,
                        "position": member.position.position_name if member.position else "специалист"
                    })

                commission.append({
                    "role": "Секретарь комиссии",
                    "name": secretary.full_name_nominative,
                    "position": secretary.position.position_name if secretary.position else "секретарь"
                })

                logger.info(f"Найдены все члены комиссии: председатель, {len(members)} членов, секретарь")
                return commission, True
            else:
                missing = []
                if not chairman:
                    missing.append("председатель")
                if not members:
                    missing.append("члены")
                if not secretary:
                    missing.append("секретарь")
                logger.warning(f"Не найдены все необходимые члены комиссии: {', '.join(missing)}")
        except Exception as e:
            logger.error(f"Ошибка при поиске членов комиссии: {str(e)}")

    # Не найдено - возвращаем отрицательный результат
    return None, False


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
    logger.warning(f"Для сотрудника {employee.full_name_nominative} не найдены документы для ознакомления")
    return None, False


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
        # Для случая отсутствия руководителя не добавляем никаких заглушек,
        # а оставляем поля пустыми, чтобы не вводить пользователя в заблуждение
        logger.error(f"Руководитель стажировки не найден для сотрудника {employee.full_name_nominative}")
        # Мы НЕ добавляем заглушки, так как это может привести к ошибкам в документе

    return context


def get_commission_formatted(employee):
    """
    Получает данные о комиссии в формате, подходящем для шаблонов документов.
    Возвращает данные только если они найдены.

    Args:
        employee: Объект модели Employee
    Returns:
        tuple: (данные о комиссии в структурированном формате, успешность выполнения)
    """
    commission_members, success = get_commission_members(employee)
    if not success or not commission_members:
        logger.warning(f"Не удалось получить данные о комиссии для сотрудника {employee.full_name_nominative}")
        # Не создаем заглушки, возвращаем пустой словарь и False
        return {}, False

    try:
        # Формируем структурированный формат
        chairman = None
        members = []
        secretary = None

        # Распределяем членов комиссии по ролям
        for member in commission_members:
            if isinstance(member, dict):
                role = member.get('role', '').lower()
                if 'председатель' in role:
                    chairman = member
                elif 'секретарь' in role:
                    secretary = member
                else:
                    members.append(member)

        # Создаем форматированные данные
        result = {}

        if chairman:
            result['chairman'] = f"{chairman['name']}, {chairman['position']}"
            result['chairman_position'] = chairman['position']
            result['chairman_name'] = chairman['name']
            result['chairman_name_initials'] = get_initials_from_name(chairman['name'])

        if members:
            result['members'] = [f"{m['name']}, {m['position']}" for m in members]
            if len(members) > 0:
                result['member1_position'] = members[0]['position']
                result['member1_name'] = members[0]['name']
                result['member1_name_initials'] = get_initials_from_name(members[0]['name'])

        if secretary:
            result['secretary'] = f"{secretary['name']}, {secretary['position']}"
            result['secretary_position'] = secretary['position']
            result['secretary_name'] = secretary['name']
            result['secretary_name_initials'] = get_initials_from_name(secretary['name'])

        # Проверяем, все ли данные заполнены
        required_keys = ['chairman', 'members', 'secretary',
                         'chairman_position', 'chairman_name', 'chairman_name_initials',
                         'member1_position', 'member1_name', 'member1_name_initials',
                         'secretary_position', 'secretary_name', 'secretary_name_initials']

        missing_keys = [key for key in required_keys if key not in result]
        if missing_keys:
            logger.warning(f"В данных комиссии отсутствуют ключи: {', '.join(missing_keys)}")
            return result, False  # Возвращаем данные, но с флагом неуспешности

        return result, True
    except Exception as e:
        logger.error(f"Ошибка при форматировании данных комиссии: {str(e)}")
        return {}, False