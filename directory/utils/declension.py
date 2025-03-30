import pymorphy2
import re

# Создаем анализатор морфологии один раз при импорте модуля
morph = pymorphy2.MorphAnalyzer()

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
    Определяет пол по ФИО (в основном по отчеству)
    """
    parts = full_name.split()
    if len(parts) >= 3:
        patronymic = parts[2].lower()
        if patronymic.endswith('вич') or patronymic.endswith('ич'):
            return 'masc'
        elif patronymic.endswith('вна') or patronymic.endswith('чна') or patronymic.endswith('шна'):
            return 'femn'

    if len(parts) >= 2:
        first_name = parts[1].lower()
        male_endings = ['й', 'н', 'р', 'т', 'м', 'к', 'п', 'с', 'л', 'в', 'д', 'б']
        female_endings = ['а', 'я', 'ь']
        if any(first_name.endswith(e) for e in male_endings) and not any(first_name.endswith(e) for e in female_endings):
            return 'masc'
        elif any(first_name.endswith(e) for e in female_endings):
            return 'femn'
    return 'masc'


def decline_word_to_case(word: str, target_case: str, gender: str = None) -> str:
    """
    Склоняет одно слово в заданный падеж.
    
    Если gender не указан (None), то пол не учитывается – для склонения фраз.
    Если gender указан (например, 'masc' или 'femn'), то он используется – для ФИО.
    """
    parse_results = morph.parse(word)
    if not parse_results:
        return word

    parse = parse_results[0]
    
    # Если пол задан и нужно скорректировать фамилию для женского пола
    if gender == 'femn' and any(tag in parse.tag for tag in ['Surn', 'NOUN']):
        try:
            if hasattr(parse, 'feminize'):
                femn_form = parse.feminize()
                if femn_form:
                    parse = femn_form
        except AttributeError:
            pass

    # Формируем набор граммем для склонения
    target_tags = {target_case}
    if gender:
        target_tags.add(gender)
    
    form = parse.inflect(target_tags)
    return form.word if form else word


def decline_full_name(full_name: str, target_case: str) -> str:
    """
    Склоняет ФИО с учетом пола.
    Здесь пол вычисляется и передается в каждое слово.
    """
    if target_case == 'nomn':
        return full_name

    gender = get_gender_from_name(full_name)
    parts = full_name.split()
    declined_parts = []
    for part in parts:
        declined_word = decline_word_to_case(part, target_case, gender)
        # Для ФИО приводим первую букву к верхнему регистру
        if declined_word:
            declined_word = declined_word[0].upper() + declined_word[1:]
        declined_parts.append(declined_word)
    return " ".join(declined_parts)


def decline_phrase(phrase: str, target_case: str) -> str:
    """
    Склоняет фразу (например, должность) в нужный падеж.
    Здесь пол не задаем – пусть pymorphy2 подбирает нужную форму.
    """
    if target_case == 'nomn':
        return phrase

    parts = phrase.split()
    declined_parts = []
    for part in parts:
        # Вызываем без передачи gender (будет None)
        declined_word = decline_word_to_case(part, target_case)
        declined_parts.append(declined_word)
    return " ".join(declined_parts)


def get_all_cases(text: str, is_full_name: bool = False) -> dict:
    result = {}
    for case_code in CASE_CODES:
        if is_full_name:
            result[case_code] = decline_full_name(text, case_code)
        else:
            result[case_code] = decline_phrase(text, case_code)
    return result


def get_initials_from_name(full_name: str) -> str:
    parts = full_name.split()
    if len(parts) < 2:
        return full_name
    surname = parts[0]
    if surname:
        surname = surname[0].upper() + surname[1:].lower()
    initials = "".join(part[0].upper() + "." for part in parts[1:] if part)
    return f"{surname} {initials}"
