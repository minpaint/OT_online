"""
🔤 Модуль для склонения слов и фраз

Этот модуль содержит функции для склонения ФИО, должностей и других фраз
в различные падежи с использованием библиотеки pymorphy2.
"""
import pymorphy2
import re

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


def get_gender_from_name(full_name: str) -> str:
    """
    Определяет пол по имени (в основном по отчеству)

    Args:
        full_name (str): ФИО в именительном падеже

    Returns:
        str: 'masc' или 'femn'
    """
    parts = full_name.split()
    if len(parts) >= 3:  # Есть отчество
        patronymic = parts[2].lower()
        if patronymic.endswith('вич') or patronymic.endswith('ич'):
            return 'masc'
        elif patronymic.endswith('вна') or patronymic.endswith('чна') or patronymic.endswith('шна'):
            return 'femn'

    # Если не удалось определить по отчеству, пробуем по имени
    if len(parts) >= 2:
        first_name = parts[1].lower()
        male_endings = ['й', 'н', 'р', 'т', 'м', 'к', 'п', 'с', 'л', 'в', 'д', 'б']
        female_endings = ['а', 'я', 'ь']

        if any(first_name.endswith(ending) for ending in male_endings) and not any(first_name.endswith(ending) for ending in female_endings):
            return 'masc'
        elif any(first_name.endswith(ending) for ending in female_endings):
            return 'femn'

    # По умолчанию - мужской род
    return 'masc'


def decline_word_to_case(word: str, target_case: str, gender: str = 'masc') -> str:
    """
    Склоняет одно слово в нужный падеж с учетом рода.

    Args:
        word (str): Исходное слово в именительном падеже
        target_case (str): Код падежа ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct')
        gender (str): Грамматический род ('masc' - мужской, 'femn' - женский)

    Returns:
        str: Склоненное слово
    """
    # Парсим слово
    parse_results = morph.parse(word)
    if not parse_results:
        return word

    # Выбираем наиболее вероятный вариант
    parse = parse_results[0]

    # Для фамилий проверяем, нужно ли сначала создать женскую форму
    if gender == 'femn' and any(tag in parse.tag for tag in ['Surn', 'NOUN']):
        # Пытаемся получить женскую форму фамилии
        try:
            # Проверяем наличие метода feminize
            if hasattr(parse, 'feminize'):
                femn_form = parse.feminize()
                if femn_form:
                    parse = femn_form
        except AttributeError:
            # Если метода нет или произошла ошибка, продолжаем без изменений
            pass

    # Приводим к нужному падежу
    form = parse.inflect({target_case, gender})

    # Если форма найдена, возвращаем её, иначе - исходное слово
    return form.word if form else word


def decline_full_name(full_name: str, target_case: str) -> str:
    """
    Склоняет ФИО в нужный падеж с учетом пола.

    Args:
        full_name (str): ФИО в именительном падеже (например, 'Иванов Иван Иванович')
        target_case (str): Код падежа ('nomn', 'gent', 'datv', 'accs', 'ablt', 'loct')

    Returns:
        str: Склоненное ФИО
    """
    # Если падеж именительный, возвращаем исходное ФИО
    if target_case == 'nomn':
        return full_name

    # Определяем пол
    gender = get_gender_from_name(full_name)

    # Разбиваем ФИО на части
    parts = full_name.split()

    # Склоняем каждую часть с учетом пола
    declined_parts = []
    for i, part in enumerate(parts):
        # Склоняем слово и приводим первую букву к верхнему регистру
        declined_word = decline_word_to_case(part, target_case, gender)
        # Приводим первую букву к верхнему регистру
        if declined_word:
            declined_word = declined_word[0].upper() + declined_word[1:]
        declined_parts.append(declined_word)

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
    # Если падеж именительный, возвращаем исходную фразу
    if target_case == 'nomn':
        return phrase

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

    # Обеспечиваем правильный регистр для фамилии
    surname = parts[0]
    if surname and len(surname) > 0:
        surname = surname[0].upper() + surname[1:].lower()

    initials = ""

    for part in parts[1:]:
        if part and len(part) > 0:
            # Убеждаемся, что инициалы заглавные
            initials += part[0].upper() + "."

    return f"{surname} {initials}"