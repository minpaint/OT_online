# directory/middleware/access_cache.py
"""
Middleware для инициализации request-level кеша прав доступа.

Кеш хранится в атрибутах request и автоматически очищается после каждого запроса.
Это решает проблему множественных обращений к БД для проверки прав в рамках одного HTTP запроса.
"""


class AccessCacheMiddleware:
    """
    Инициализирует кеш прав доступа для каждого запроса.

    Добавляет в request следующие атрибуты:
    - _user_orgs_cache: QuerySet доступных организаций
    - _user_subdivs_cache: QuerySet доступных подразделений
    - _user_depts_cache: QuerySet доступных отделов

    Эти атрибуты заполняются лениво (при первом обращении) в AccessControlHelper.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Инициализируем кеш перед обработкой запроса
        request._user_orgs_cache = None
        request._user_subdivs_cache = None
        request._user_depts_cache = None

        # Обрабатываем запрос
        response = self.get_response(request)

        # Кеш автоматически очищается после запроса (GC)

        return response
