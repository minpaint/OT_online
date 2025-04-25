from django.urls import resolve
from django.urls.exceptions import Resolver404

# Проверяем различные варианты URL, которые могут отображать список должностей
urls_to_check = [
    '/directory/positions/',
    '/directory/professions/',
    '/directory/position/',
    '/directory/profession/',
    '/directory/position/list/',
    '/directory/positions/list/',
]

for url in urls_to_check:
    try:
        view_func = resolve(url).func
        print(f"URL: {url} -> {view_func}")
        if hasattr(view_func, 'view_class'):
            view_class = view_func.view_class
            print(f"View класс: {view_class.__name__}")
            if hasattr(view_class, 'template_name'):
                print(f"Шаблон: {view_class.template_name}")
    except Resolver404:
        print(f"URL {url} не найден")

# Можно также посмотреть все URL паттерны
from django.urls import get_resolver
resolver = get_resolver()
for pattern in resolver.url_patterns:
    if hasattr(pattern, 'name') and 'position' in pattern.name:
        print(f"Pattern: {pattern.name} -> {pattern.callback}")
