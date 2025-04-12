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

# --- Новые/обновленные функции ---

def format_commission_member(employee):
    """
    Форматирует информацию о члене комиссии в строку вида "ФИО, должность"
    Args:
        employee: Объект сотрудника Employee
    Returns:
        str: Строка вида "Иванов И.И., директор"
    """
    from directory.utils.declension import get_initials_from_name
    from directory.models import Employee # Ensure Employee is available if not globally imported

    if not isinstance(employee, Employee):
        logger.error(f"Invalid type passed to format_commission_member: {type(employee)}")
        return "Ошибка формата" # Or handle appropriately

    position_name = ""
    if employee.position:
        position_name = employee.position.position_name.lower()

    # Получаем инициалы
    # Ensure full_name_nominative exists and is a string
    name_initials = ""
    if hasattr(employee, 'full_name_nominative') and isinstance(employee.full_name_nominative, str):
         name_initials = get_initials_from_name(employee.full_name_nominative)
    else:
         logger.warning(f"Employee {employee.id} has no full_name_nominative or it's not a string.")


    # Формируем строку вида "Иванов И.И., директор"
    return f"{name_initials}, {position_name}" if position_name else name_initials

def default_commission():
    """
    Возвращает значения по умолчанию для комиссии (НЕ ИСПОЛЬЗУЕТСЯ в get_commission_members)
    Returns:
        dict: Словарь с данными комиссии по умолчанию
    """
    return {
        'chairman': "Иванов И.И., директор",
        'members': ["Петров П.П., зам. директора", "Сидоров С.С., инженер по ОТ"],
        'secretary': "Кузнецова К.К., секретарь"
    }

def get_commission_members(employee):
    """
    Получает список членов комиссии для протокола проверки знаний.
    Поиск ВСЕХ ролей (chairman, member, secretary) выполняется
    напрямую в организации сотрудника,
    у которых в должности указана соответствующая роль commission_role.
    (Подразумевается, что неактивные сотрудники не должны иметь таких ролей
    или должны быть удалены из системы)

    Args:
        employee: Объект сотрудника Employee
    Returns:
        tuple: (members_list, success) - members_list содержит найденных членов в виде словарей,
               success=True если найдены председатель, секретарь и хотя бы 1 член.
    """
    from directory.models import Employee # Ensure Employee is available
    import logging # Ensure logging is available

    logger = logging.getLogger(__name__) # Ensure logger is initialized

    # Проверяем организацию
    if not employee.organization:
        logger.warning(f"У сотрудника {employee.pk} ({employee.full_name_nominative}) не указана организация")
        return [], False

    organization = employee.organization
    commission = {
        'chairman': None,
        'members': [],
        'secretary': None
    }
    chairman_found_obj = None
    members_found_objs = []
    secretary_found_obj = None
    # Get organization name safely for logging, falling back to ID
    organization_name_for_log = getattr(organization, 'name', None) # Use getattr for safety
    if organization_name_for_log is None and hasattr(organization, 'full_name'): # Check for full_name if name is missing
         organization_name_for_log = getattr(organization, 'full_name', str(organization.id))
    elif organization_name_for_log is None: # Fallback to ID if neither name nor full_name exists
         organization_name_for_log = str(organization.id)


    # 1. Ищем председателя комиссии ВО ВСЕЙ ОРГАНИЗАЦИИ
    try:
        chairman_found_obj = Employee.objects.filter(
            organization=organization,
            position__commission_role='chairman' # Removed is_active=True
        ).select_related('position').first()
        if chairman_found_obj:
            commission['chairman'] = format_commission_member(chairman_found_obj)
            logger.info(f"Найден председатель во всей организации: {commission['chairman']}")
        else:
             logger.warning(f"Председатель комиссии не найден во всей организации {organization_name_for_log}")
    except Exception as e:
        # Log the error with traceback
        logger.error(f"Ошибка при поиске председателя комиссии в организации {organization_name_for_log}: {e}", exc_info=True)


    # 2. Ищем членов комиссии ВО ВСЕЙ ОРГАНИЗАЦИИ
    try:
        members_found_objs = list(Employee.objects.filter(
            organization=organization,
            position__commission_role='member' # Removed is_active=True
        ).select_related('position'))
        commission['members'] = [format_commission_member(m) for m in members_found_objs]
        logger.info(f"Найдено членов комиссии во всей организации: {len(commission['members'])}")
        if not commission['members']:
            logger.warning(f"Члены комиссии не найдены во всей организации {organization_name_for_log}")
    except Exception as e:
        logger.error(f"Ошибка при поиске членов комиссии в организации {organization_name_for_log}: {e}", exc_info=True)


    # 3. Ищем секретаря комиссии ВО ВСЕЙ ОРГАНИЗАЦИИ
    try:
        secretary_found_obj = Employee.objects.filter(
            organization=organization,
            position__commission_role='secretary' # Removed is_active=True
        ).select_related('position').first()
        if secretary_found_obj:
            commission['secretary'] = format_commission_member(secretary_found_obj)
            logger.info(f"Найден секретарь во всей организации: {commission['secretary']}")
        else:
             logger.warning(f"Секретарь комиссии не найден во всей организации {organization_name_for_log}")
    except Exception as e:
        logger.error(f"Ошибка при поиске секретаря комиссии в организации {organization_name_for_log}: {e}", exc_info=True)


    # Проверяем, удалось ли найти минимально необходимый состав
    success = (
        commission['chairman'] is not None and
        len(commission['members']) >= 1 and
        commission['secretary'] is not None
    )

    if not success:
        logger.warning(
            f"Не удалось найти полный минимальный состав комиссии для {employee.full_name_nominative} в организации {organization_name_for_log}. "
            f"Найдено: председатель={'Да' if commission['chairman'] else 'Нет'}, "
            f"членов={len(commission['members'])}, "
            f"секретарь={'Да' if commission['secretary'] else 'Нет'}"
        )

    # Преобразуем результат в список словарей для get_commission_formatted
    result = []

    # Добавляем председателя, если найден
    if chairman_found_obj:
        result.append({
            "role": "Председатель комиссии",
            "name": commission['chairman'], # Уже содержит должность
            "employee_obj": chairman_found_obj
        })

    # Добавляем членов комиссии, если найдены
    for idx, member_str in enumerate(commission['members']):
         if idx < len(members_found_objs): # Защита от рассогласования
            member_obj = members_found_objs[idx] # Получаем объект Employee
            result.append({
                "role": "Член комиссии",
                "name": member_str, # Уже содержит должность
                "employee_obj": member_obj
            })

    # Добавляем секретаря, если найден
    if secretary_found_obj:
        result.append({
            "role": "Секретарь комиссии",
            "name": commission['secretary'], # Уже содержит должность
            "employee_obj": secretary_found_obj
        })

    # Возвращаем список найденных членов и флаг успеха (полный ли состав)
    return result, success

# --- Остальной код файла ---

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
    во всех падежах для более гибкого использования в шаблонах.

    Args:
        employee: Объект сотрудника Employee
    Returns:
        dict: Обновленный контекст с добавленными данными о стажировке
    """
    if context is None:
        context = {}

    # Получаем информацию о руководителе стажировки
    leader, level, success = get_internship_leader(employee)

    if success and leader:
        # Получаем должность и имя в именительном падеже
        leader_position = leader.position.position_name if leader.position else ""
        leader_name = leader.full_name_nominative

        # Преобразуем первую букву должности в нижний регистр
        if leader_position:
            leader_position = leader_position[0].lower() + leader_position[1:]

        # Получаем инициалы
        leader_name_initials = get_initials_from_name(leader_name)

        # Склоняем имя и должность во всех падежах для гибкости использования
        # Именительный (nomn) - уже есть
        # Родительный (gent)
        leader_position_genitive = decline_phrase(leader_position, 'gent') if leader_position else ""
        leader_name_genitive = decline_full_name(leader_name, 'gent')

        # Дательный (datv)
        leader_position_dative = decline_phrase(leader_position, 'datv') if leader_position else ""
        leader_name_dative = decline_full_name(leader_name, 'datv')

        # Винительный (accs)
        leader_position_accusative = decline_phrase(leader_position, 'accs') if leader_position else ""
        leader_name_accusative = decline_full_name(leader_name, 'accs')

        # Творительный (ablt)
        leader_position_instrumental = decline_phrase(leader_position, 'ablt') if leader_position else ""
        leader_name_instrumental = decline_full_name(leader_name, 'ablt')

        # Предложный (loct)
        leader_position_prepositional = decline_phrase(leader_position, 'loct') if leader_position else ""
        leader_name_prepositional = decline_full_name(leader_name, 'loct')

        # Добавляем в контекст оригинальные и склоненные варианты
        context.update({
            # Именительный падеж (кто? что?)
            'head_of_internship_position': leader_position,
            'head_of_internship_name': leader_name,
            'head_of_internship_name_initials': leader_name_initials,

            # Родительный падеж (кого? чего?)
            'head_of_internship_position_genitive': leader_position_genitive,
            'head_of_internship_name_genitive': leader_name_genitive,

            # Дательный падеж (кому? чему?)
            'head_of_internship_position_dative': leader_position_dative,
            'head_of_internship_name_dative': leader_name_dative,

            # Винительный падеж (кого? что?)
            'head_of_internship_position_accusative': leader_position_accusative,
            'head_of_internship_name_accusative': leader_name_accusative,

            # Творительный падеж (кем? чем?)
            'head_of_internship_position_instrumental': leader_position_instrumental,
            'head_of_internship_name_instrumental': leader_name_instrumental,

            # Предложный падеж (о ком? о чём?)
            'head_of_internship_position_prepositional': leader_position_prepositional,
            'head_of_internship_name_prepositional': leader_name_prepositional,

            # Служебная информация
            'internship_leader_level': level,
        })

        # Добавляем лог об успешном склонении
        logger.info(f"Подготовлен контекст руководителя стажировки во всех падежах для {employee.full_name_nominative}")
    else:
        # Для случая отсутствия руководителя не добавляем никаких заглушек,
        # а оставляем поля пустыми, чтобы не вводить пользователя в заблуждение
        logger.error(f"Руководитель стажировки не найден для сотрудника {employee.full_name_nominative}")
        # Мы НЕ добавляем заглушки, так как это может привести к ошибкам в документе

    return context


def prepare_director_context(employee, context=None):
    """
    Подготавливает контекст для подписанта документа (директора),
    включая склонение имени и должности во всех падежах.

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
        signer_position = signer.position.position_name if signer.position else ""
        signer_name = signer.full_name_nominative

        # Получаем инициалы
        signer_name_initials = get_initials_from_name(signer_name)

        # Склоняем имя и должность во всех падежах
        # Именительный (nomn) - уже есть
        # Родительный (gent)
        signer_position_genitive = decline_phrase(signer_position, 'gent') if signer_position else ""
        signer_name_genitive = decline_full_name(signer_name, 'gent')

        # Дательный (datv)
        signer_position_dative = decline_phrase(signer_position, 'datv') if signer_position else ""
        signer_name_dative = decline_full_name(signer_name, 'datv')

        # Винительный (accs)
        signer_position_accusative = decline_phrase(signer_position, 'accs') if signer_position else ""
        signer_name_accusative = decline_full_name(signer_name, 'accs')

        # Творительный (ablt)
        signer_position_instrumental = decline_phrase(signer_position, 'ablt') if signer_position else ""
        signer_name_instrumental = decline_full_name(signer_name, 'ablt')

        # Предложный (loct)
        signer_position_prepositional = decline_phrase(signer_position, 'loct') if signer_position else ""
        signer_name_prepositional = decline_full_name(signer_name, 'loct')

        context.update({
            # Именительный падеж
            'director_position': signer_position,
            'director_name': signer_name,
            'director_name_initials': signer_name_initials,

            # Родительный падеж
            'director_position_genitive': signer_position_genitive,
            'director_name_genitive': signer_name_genitive,

            # Дательный падеж
            'director_position_dative': signer_position_dative,
            'director_name_dative': signer_name_dative,

            # Винительный падеж
            'director_position_accusative': signer_position_accusative,
            'director_name_accusative': signer_name_accusative,

            # Творительный падеж
            'director_position_instrumental': signer_position_instrumental,
            'director_name_instrumental': signer_name_instrumental,

            # Предложный падеж
            'director_position_prepositional': signer_position_prepositional,
            'director_name_prepositional': signer_name_prepositional,

            # Служебная информация
            'director_level': level,
        })

        logger.info(f"Подготовлен контекст подписанта документа во всех падежах для {employee.full_name_nominative}")
    else:
        # Если подписант не найден - не добавляем заглушки
        logger.error(f"Подписант документа не найден для сотрудника {employee.full_name_nominative}")

    return context


def get_commission_formatted(employee):
    """
    Получает данные о комиссии в формате, подходящем для шаблонов документов.
    Возвращает данные только если они найдены и состав комиссии полный.
    Также добавляет склонения для членов комиссии.

    Args:
        employee: Объект модели Employee
    Returns:
        tuple: (данные о комиссии в структурированном формате, успешность выполнения)
    """
    commission_members_list, success = get_commission_members(employee)

    # Возвращаем пустые данные, если комиссия не найдена ИЛИ состав неполный
    if not success or not commission_members_list:
        logger.warning(f"Не удалось получить полный состав комиссии для сотрудника {employee.full_name_nominative}")
        # Не создаем заглушки, возвращаем пустой словарь и False
        return {}, False

    try:
        # Формируем структурированный формат и добавляем склонения
        result = {}
        members_formatted = []

        for member_data in commission_members_list:
            role_key = member_data.get('role', '').lower()
            member_obj = member_data.get('employee_obj') # Получаем объект сотрудника

            if not member_obj:
                logger.warning(f"Отсутствует объект сотрудника для члена комиссии: {member_data.get('name')}")
                continue # Пропускаем, если нет объекта

            name = member_obj.full_name_nominative
            position = member_obj.position.position_name if member_obj.position else ""
            name_initials = get_initials_from_name(name)

            # Базовые данные
            member_info = {
                "name": name,
                "position": position,
                "name_initials": name_initials,
                "formatted": f"{name_initials}, {position.lower()}" if position else name_initials
            }

            # Склонения
            try:
                member_info.update({
                    'position_genitive': decline_phrase(position, 'gent') if position else "",
                    'name_genitive': decline_full_name(name, 'gent'),
                    'position_dative': decline_phrase(position, 'datv') if position else "",
                    'name_dative': decline_full_name(name, 'datv'),
                    'position_accusative': decline_phrase(position, 'accs') if position else "",
                    'name_accusative': decline_full_name(name, 'accs'),
                    'position_instrumental': decline_phrase(position, 'ablt') if position else "",
                    'name_instrumental': decline_full_name(name, 'ablt'),
                    'position_prepositional': decline_phrase(position, 'loct') if position else "",
                    'name_prepositional': decline_full_name(name, 'loct'),
                })
            except Exception as e:
                 logger.error(f"Ошибка склонения для {name}, {position}: {e}")
                 # Можно добавить пустые строки или оставить как есть

            # Распределяем по ролям
            if 'председатель' in role_key:
                result['chairman'] = member_info['formatted']
                for k, v in member_info.items():
                    result[f'chairman_{k}'] = v
            elif 'секретарь' in role_key:
                result['secretary'] = member_info['formatted']
                for k, v in member_info.items():
                    result[f'secretary_{k}'] = v
            else: # Член комиссии
                members_formatted.append(member_info)


        # Обрабатываем членов комиссии
        if members_formatted:
            result['members'] = [m['formatted'] for m in members_formatted]
            # Добавляем данные для первого члена комиссии (для шаблонов)
            if len(members_formatted) > 0:
                member1_info = members_formatted[0]
                result['member1'] = member1_info['formatted']
                for k, v in member1_info.items():
                    result[f'member1_{k}'] = v

            # Добавляем полный список форматированных членов для нового шаблона
            result['members_formatted'] = members_formatted # Добавляем список словарей

        # Еще раз проверяем наличие обязательных ключей ПОСЛЕ обработки
        # success уже гарантирует, что chairman, secretary и хотя бы 1 member БЫЛИ НАЙДЕНЫ
        # Эта проверка нужна, если при форматировании что-то пошло не так
        required_keys_in_result = ['chairman', 'members', 'secretary']
        missing_keys = [key for key in required_keys_in_result if key not in result]
        if missing_keys:
            logger.warning(f"В итоговых данных комиссии отсутствуют ключи: {', '.join(missing_keys)}")
            # Возвращаем то, что есть, но с флагом неуспешности
            return result, False

        logger.info(f"Успешно сформированы данные комиссии для {employee.full_name_nominative}")
        return result, True # Успех, так как success был True и форматирование прошло

    except Exception as e:
        logger.exception(f"Ошибка при форматировании данных комиссии: {e}") # Используем exception для стектрейса
        return {}, False
