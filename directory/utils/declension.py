"""
🔤 Модуль для склонения слов и фраз

Этот модуль содержит функции для склонения ФИО, должностей и других фраз
в различные падежи с использованием библиотеки pymorphy2.
"""
import pymorphy2

# Создаем анализатор морфологии один раз при импорте модуля
morph = pymorphy2.MorphAnalyzer()

# Словарь с кодами падежей и их названиями для справки
CASE_CODES = {
    'nomn': 'именительный',  # Кто? Что? (работает Иванов)
    'gent': 'родительный',   # Кого? Чего? (нет Иванова)
    'datv': 'дательный',     # Кому? Чему? (дать Иванову)
    'accs': 'винительный',   # Кого? Что? (вижу Иванова)
    'ablt': 'творительный',  # Кем? Чем? (доволен Ивановым)
    'loct': 'предложный'     # О ком? О чем? (думаю об Иванове)
}

def decline_word_to_case(word: str, target_case: str) -> str:
    """
    Склоняет одно слово в нужный падеж.

    Args:
        word (str): Исходное слово в именительном падеже
        target_case (str): Код падежа ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct')

    Returns:
        str: Склоненное слово
    """
    # Парсим слово
    parse = morph.parse(word)[0]

    # Приводим к нужному падежу
    form = parse.inflect({target_case})

    # Если форма найдена, возвращаем её, иначе - исходное слово
    return form.word if form else word


def decline_full_name(full_name: str, target_case: str) -> str:
    """
    Склоняет ФИО в нужный падеж.

    Args:
        full_name (str): ФИО в именительном падеже (например, 'Иванов Иван Иванович')
        target_case (str): Код падежа ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct')

    Returns:
        str: Склоненное ФИО
    """
    # Разбиваем ФИО на части
    parts = full_name.split()

    # Склоняем каждую часть
    declined_parts = []
    for part in parts:
        declined_parts.append(decline_word_to_case(part, target_case))

    # Собираем обратно в строку
    return " ".join(declined_parts)


def decline_phrase(phrase: str, target_case: str) -> str:
    """
    Склоняет фразу (например, название должности) в нужный падеж.

    Args:
        phrase (str): Фраза в именительном падеже (например, 'Старший специалист')
        target_case (str): Код падежа ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct')

    Returns:
        str: Склоненная фраза
    """
    # Разбиваем фразу на слова
    parts = phrase.split()

    # Склоняем каждое слово
    declined_parts = []
    for part in parts:
        declined_parts.append(decline_word_to_case(part, target_case))

    # Собираем обратно в строку
    return " ".join(declined_parts)


def get_all_cases(text: str, is_full_name: bool = False) -> dict:
    """
    Получает все падежные формы для текста.

    Args:
        text (str): Исходный текст в именительном падеже
        is_full_name (bool): Флаг, указывающий, является ли текст ФИО

    Returns:
        dict: Словарь с падежными формами
    """
    result = {}

    for case_code, case_name in CASE_CODES.items():
        if is_full_name:
            result[case_code] = decline_full_name(text, case_code)
        else:
            result[case_code] = decline_phrase(text, case_code)

    return result


def get_initials_from_name(full_name: str) -> str:
    """
    Получает инициалы из полного имени (Фамилия И.О.).

    Args:
        full_name (str): Полное имя в формате 'Фамилия Имя Отчество'

    Returns:
        str: Имя с инициалами (Фамилия И.О.)
    """
    parts = full_name.split()

    if len(parts) < 2:
        return full_name

    surname = parts[0]
    initials = ""

    for part in parts[1:]:
        if part:
            initials += part[0] + "."

    return f"{surname} {initials}"