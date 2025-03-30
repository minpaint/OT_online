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
    Определяет пол по ФИО (в основном по отчеству).
    Возвращает 'masc' (мужской) или 'femn' (женский).
    """
    parts = full_name.split()
    if len(parts) >= 3:  # Если есть отчество
        patronymic = parts[2].lower()
        if patronymic.endswith('вич') or patronymic.endswith('ич'):
            return 'masc'
        elif patronymic.endswith('вна') or patronymic.endswith('чна') or patronymic.endswith('шна'):
            return 'femn'

    # Если отчества нет или оно неполное, пробуем угадать по имени
    if len(parts) >= 2:
        first_name = parts[1].lower()
        male_endings = ['й', 'н', 'р', 'т', 'м', 'к', 'п', 'с', 'л', 'в', 'д', 'б']
        female_endings = ['а', 'я', 'ь']
        if any(first_name.endswith(e) for e in male_endings) and not any(first_name.endswith(e) for e in female_endings):
            return 'masc'
        elif any(first_name.endswith(e) for e in female_endings):
            return 'femn'

    # По умолчанию - мужской род
    return 'masc'


def decline_word_to_case(word: str, target_case: str, gender: str = None) -> str:
    """
    Склоняет одно слово в заданный падеж. Если gender=None,
    pymorphy2 подбирает форму без учёта пола (для фраз).
    Если gender='masc'/'femn', то учитываем род (для ФИО).
    """
    parse_results = morph.parse(word)
    if not parse_results:
        return word

    parse = parse_results[0]

    # Если нужно женское склонение фамилии или существительного
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
    Склоняет ФИО с учётом пола.
    Каждое из слов (Фамилия, Имя, Отчество) будет иметь первую букву заглавную.
    """
    if target_case == 'nomn':
        return full_name

    gender = get_gender_from_name(full_name)
    parts = full_name.split()
    declined_parts = []
    for part in parts:
        declined_word = decline_word_to_case(part, target_case, gender=gender)
        # Для ФИО делаем первую букву заглавной
        if declined_word:
            declined_word = declined_word[0].upper() + declined_word[1:]
        declined_parts.append(declined_word)

    return " ".join(declined_parts)


def decline_phrase(phrase: str, target_case: str) -> str:
    """
    Склоняет фразу (должность, несколько слов и т.д.) в заданный падеж.
    При этом, если слово уже не в именительном падеже (nomn), оно останется как есть.
    """
    if target_case == 'nomn':
        return phrase

    parts = phrase.split()
    declined_parts = []

    for part in parts:
        parse_results = morph.parse(part)
        if not parse_results:
            # Если pymorphy2 не распознало слово, оставляем без изменений
            declined_parts.append(part)
            continue

        parse = parse_results[0]

        # Проверяем, есть ли признак именительного падежа (nomn) в тегах
        if 'nomn' in parse.tag:
            # Только если слово в именительном падеже,
            # переводим в целевой падеж
            inflected = parse.inflect({target_case})
            if inflected:
                declined_parts.append(inflected.word)
            else:
                # Не получилось склонить – возвращаем исходное
                declined_parts.append(part)
        else:
            # Если слово уже не в именительном падеже,
            # оставляем его как есть
            declined_parts.append(part)

    return " ".join(declined_parts)


def get_all_cases(text: str, is_full_name: bool = False) -> dict:
    """
    Возвращает все падежные формы (nomn, gent, datv, accs, ablt, loct)
    для переданного текста.
    Если is_full_name=True, будет использоваться decline_full_name,
    иначе decline_phrase.
    """
    result = {}
    for case_code in CASE_CODES:
        if is_full_name:
            result[case_code] = decline_full_name(text, case_code)
        else:
            result[case_code] = decline_phrase(text, case_code)
    return result


def get_initials_from_name(full_name: str) -> str:
    """
    Преобразует ФИО в форму "Фамилия И.О."
    """
    parts = full_name.split()
    if len(parts) < 2:
        return full_name

    surname = parts[0]
    if surname:
        surname = surname[0].upper() + surname[1:].lower()

    initials = "".join(part[0].upper() + "." for part in parts[1:] if part)

    return f"{surname} {initials}"
