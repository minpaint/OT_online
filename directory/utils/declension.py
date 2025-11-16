import pymorphy3
import re

# Создаем анализатор морфологии один раз при импорте модуля
morph = pymorphy3.MorphAnalyzer()

CASE_CODES = {
    'nomn': 'именительный',  # Кто? Что? (работает Иванов)
    'gent': 'родительный',  # Кого? Чего? (нет Иванова)
    'datv': 'дательный',  # Кому? Чему? (дать Иванову)
    'accs': 'винительный',  # Кого? Что? (вижу Иванова)
    'ablt': 'творительный',  # Кем? Чем? (доволен Ивановым)
    'loct': 'предложный'  # О ком? О чем? (думаю об Иванове)
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
        if any(first_name.endswith(e) for e in male_endings) and not any(
                first_name.endswith(e) for e in female_endings):
            return 'masc'
        elif any(first_name.endswith(e) for e in female_endings):
            return 'femn'

    # По умолчанию - мужской род
    return 'masc'


def decline_word_to_case(word: str, target_case: str, gender: str = None) -> str:
    """
    Склоняет одно слово в заданный падеж.
    Если gender=None (для фраз), pymorphy2 подбирает форму без учёта пола.
    Если gender='masc'/'femn' (для ФИО), то учитываем род.
    """
    parse_results = morph.parse(word)
    if not parse_results:
        return word

    # Для ФИО (когда указан пол) ищем разбор в именительном падеже с правильным родом
    parse = parse_results[0]

    if gender:
        # Ищем разбор фамилии/имени/отчества в именительном падеже с нужным родом
        # Приоритет: правильный род > высокий score
        best_parse_with_gender = None
        best_score_with_gender = 0.0
        best_parse_any = None
        best_score_any = 0.0

        for p in parse_results:
            # Проверяем, что это именительный падеж
            if 'nomn' in p.tag:
                # Для фамилий, имён и отчеств
                is_name_part = any(tag in p.tag for tag in ['Surn', 'Name', 'Patr'])

                if not is_name_part:
                    continue

                # Проверяем совпадение рода
                gender_matches = gender in p.tag

                # Приоритет 1: именительный падеж + правильный род + это часть ФИО
                if gender_matches and p.score > best_score_with_gender:
                    best_parse_with_gender = p
                    best_score_with_gender = p.score

                # Приоритет 2: любой род, но именительный падеж и часть ФИО
                if p.score > best_score_any:
                    best_parse_any = p
                    best_score_any = p.score

        # Отдаём предпочтение разбору с правильным родом, даже если score ниже
        if best_parse_with_gender:
            parse = best_parse_with_gender
        elif best_parse_any:
            parse = best_parse_any

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


def pick_parse_in_nomn(word: str):
    """
    Возвращает наилучший разбор слова, который стоит в именительном падеже (nomn).
    Если такого нет, вернёт просто самый вероятный разбор (parse_results[0]).

    Нужен для того, чтобы мы точно взяли форму 'клиническое' (ADJF, nomn, neut, sing)
    вместо какой-нибудь другой, если pymorphy2 распознает несколько вариантов.
    """
    parses = morph.parse(word)
    if not parses:
        return None
    best_nomn = None
    best_score = 0.0

    for p in parses:
        if 'nomn' in p.tag and p.score > best_score:
            best_nomn = p
            best_score = p.score

    return best_nomn if best_nomn else parses[0]


def is_word_in_nominative(word: str) -> bool:
    """
    Проверяет, находится ли слово в именительном падеже единственного числа.
    Возвращает True только если наиболее вероятный разбор - именительный падеж
    единственного числа.
    """
    parses = morph.parse(word)
    if not parses:
        return False

    # Берём наиболее вероятный разбор
    best_parse = parses[0]

    # Проверяем, что это именительный падеж единственного числа
    # и что это не множественное число (plur)
    if 'nomn' in best_parse.tag and 'sing' in best_parse.tag:
        return True

    # Если наиболее вероятный разбор НЕ в именительном падеже единственного числа,
    # значит слово уже склонено (например, "сигнализации" - родительный падеж)
    return False


def decline_phrase(phrase: str, target_case: str) -> str:
    """
    Склоняет фразу (должность, словосочетание типа "Клиническое отделение", и т.д.)
    в заданный падеж.
    Логика:
      1) Если слово изначально не в именительном падеже единственного числа, оставляем как есть.
      2) Если слово в именительном падеже единственного числа, пытаемся склонить его в нужный.
    """
    if target_case == 'nomn':
        return phrase

    parts = phrase.split()
    declined_parts = []

    for part in parts:
        parses = morph.parse(part)
        if not parses:
            declined_parts.append(part)
            continue

        # Берём наиболее вероятный разбор
        best_parse = parses[0]

        # Проверяем, является ли слово именительным падежом единственного числа
        # Если да - склоняем, если нет - оставляем как есть (это зависимое слово)
        is_nomn_sing = 'nomn' in best_parse.tag and 'sing' in best_parse.tag

        # Дополнительная проверка: если слово может быть как nomn plur, так и gent sing,
        # и score для gent выше - не склоняем
        if 'nomn' in best_parse.tag and 'plur' in best_parse.tag:
            # Проверяем, нет ли более вероятного варианта в другом падеже единственного числа
            for p in parses:
                if 'sing' in p.tag and 'nomn' not in p.tag and p.score >= best_parse.score:
                    # Слово скорее в другом падеже единственного числа - не склоняем
                    is_nomn_sing = False
                    break

        if is_nomn_sing:
            # Склоняем в нужный падеж
            inflected = best_parse.inflect({target_case})
            if inflected:
                declined_parts.append(inflected.word)
            else:
                declined_parts.append(part)
        else:
            # Слово уже не в именительном падеже (зависимое слово) - не трогаем
            declined_parts.append(part)

    return " ".join(declined_parts)


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

    for i, part in enumerate(parts):
        # Для первого слова (фамилии) используем специальную обработку
        if i == 0:
            declined_word = decline_surname(part, target_case, gender)
        else:
            declined_word = decline_word_to_case(part, target_case, gender=gender)
        # Для ФИО делаем первую букву заглавной
        if declined_word:
            declined_word = declined_word[0].upper() + declined_word[1:]
        declined_parts.append(declined_word)

    return " ".join(declined_parts)


def decline_surname(surname: str, target_case: str, gender: str) -> str:
    """
    Склоняет фамилию с учётом её типа и пола.
    Обрабатывает редкие фамилии, которые pymorphy3 не распознаёт.
    """
    parse_results = morph.parse(surname)
    if not parse_results:
        return surname

    surname_lower = surname.lower()

    # Сначала проверяем стандартные окончания фамилий и склоняем по правилам
    # Это важно, потому что pymorphy3 может неправильно распознать редкие фамилии

    # Стандартные мужские фамилии на -ов/-ев/-ёв/-ин/-ын
    if gender == 'masc' and surname_lower.endswith(('ов', 'ев', 'ёв', 'ин', 'ын')):
        # Склоняем по правилам мужских фамилий на -ов/-ин
        endings = {
            'nomn': '',
            'gent': 'а',
            'datv': 'у',
            'accs': 'а',
            'ablt': 'ым',
            'loct': 'е',
        }
        if target_case in endings:
            return surname + endings[target_case]

    # Стандартные женские фамилии на -ова/-ева/-ёва/-ина/-ына
    if gender == 'femn' and surname_lower.endswith(('ова', 'ева', 'ёва', 'ина', 'ына')):
        # Склоняем по правилам женских фамилий на -ова/-ина
        # Убираем последнюю букву 'а' и добавляем окончание
        base = surname[:-1]  # Петрова -> Петров
        endings = {
            'nomn': 'а',
            'gent': 'ой',
            'datv': 'ой',
            'accs': 'у',
            'ablt': 'ой',
            'loct': 'ой',
        }
        if target_case in endings:
            return base + endings[target_case]

    # Пробуем найти разбор как фамилию (Surn) в pymorphy3
    best_parse = None
    for p in parse_results:
        if 'Surn' in p.tag and 'nomn' in p.tag and gender in p.tag:
            best_parse = p
            break
        elif 'Surn' in p.tag and 'nomn' in p.tag:
            best_parse = p

    if best_parse:
        # Нашли как фамилию - склоняем стандартно
        form = best_parse.inflect({target_case, gender})
        return form.word if form else surname

    # Фамилии на -а/-я (Симака, Пётра, и т.д.) - склоняются как сущ. 1 склонения
    if surname_lower.endswith(('а', 'я')) and not surname_lower.endswith(('ова', 'ева', 'ина', 'ына')):
        # Ищем разбор как существительное женского рода в именительном падеже
        for p in parse_results:
            if 'NOUN' in p.tag and 'femn' in p.tag and 'nomn' in p.tag and 'sing' in p.tag:
                form = p.inflect({target_case})
                if form:
                    return form.word
        # Если не нашли, пробуем склонять как любое существительное на -а
        for p in parse_results:
            if 'NOUN' in p.tag and 'nomn' in p.tag and 'sing' in p.tag:
                form = p.inflect({target_case})
                if form:
                    return form.word

    # Несклоняемые фамилии (на -о, -е, -и, -у, -ю, иностранные)
    if surname_lower.endswith(('о', 'е', 'и', 'у', 'ю', 'ых', 'их')):
        return surname

    # Если ничего не подошло, используем стандартную функцию
    return decline_word_to_case(surname, target_case, gender)


def get_all_cases(text: str, is_full_name: bool = False) -> dict:
    """
    Возвращает все падежные формы (nomn, gent, datv, accs, ablt, loct)
    для переданного текста.

    Если is_full_name=True, будет использоваться decline_full_name (учёт пола, заглавные буквы).
    Если is_full_name=False, будет использоваться decline_phrase (общая фраза).
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


def get_initials_before_surname(full_name: str) -> str:
    """
    Преобразует ФИО в форму "И.О. Фамилия"

    Используется для подписей в протоколах и актах комиссий.

    Примеры:
        "Демешко Павел Владимирович" -> "П.В. Демешко"
        "Иванов Иван Иванович" -> "И.И. Иванов"
    """
    parts = full_name.split()
    if len(parts) < 2:
        return full_name

    surname = parts[0]
    if surname:
        surname = surname[0].upper() + surname[1:].lower()

    initials = "".join(part[0].upper() + "." for part in parts[1:] if part)

    return f"{initials} {surname}"


def pluralize_days(number: int) -> str:
    """
    Возвращает правильную форму слова 'день' для заданного числа.

    Примеры:
    - 1 день
    - 2, 3, 4 дня
    - 5-20 дней
    - 21 день
    - 22, 23, 24 дня
    - 25-30 дней
    """
    # Обрабатываем отрицательные числа
    number = abs(number)

    # Последние две цифры для определения исключений (11-19)
    last_two = number % 100

    # Последняя цифра
    last_one = number % 10

    if 11 <= last_two <= 19:
        # Исключение: 11-19 -> "дней"
        return "дней"
    elif last_one == 1:
        # 1, 21, 31, ... -> "день"
        return "день"
    elif 2 <= last_one <= 4:
        # 2, 3, 4, 22, 23, 24, ... -> "дня"
        return "дня"
    else:
        # 0, 5, 6, 7, 8, 9, 10, 25, 26, ... -> "дней"
        return "дней"


def format_days(number: int) -> str:
    """
    Форматирует число с правильной формой слова 'день'.

    Примеры:
    - format_days(1) -> "1 день"
    - format_days(2) -> "2 дня"
    - format_days(5) -> "5 дней"
    - format_days(21) -> "21 день"
    """
    return f"{number} {pluralize_days(number)}"
