"""
Middleware для защиты от индексации поисковыми системами.

Добавляет HTTP-заголовки X-Robots-Tag ко всем ответам для блокировки индексации.
Также обрабатывает запросы к robots.txt.

Автор: Система OT_online
"""

from django.http import HttpResponse
from django.conf import settings


class AntiIndexationMiddleware:
    """
    Middleware для защиты всего сайта от индексации поисковыми системами.

    Функции:
    1. Добавляет X-Robots-Tag заголовок ко всем ответам
    2. Обрабатывает запросы к /robots.txt
    3. Работает как для основного домена, так и для поддоменов
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Обработка robots.txt - возвращаем статический файл
        if request.path == '/robots.txt':
            return self._serve_robots_txt()

        # 2. Обрабатываем запрос
        response = self.get_response(request)

        # 3. Добавляем X-Robots-Tag ко всем ответам
        # (даже если есть meta-теги, заголовок усиливает защиту)
        response['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'

        # 4. Дополнительные заголовки безопасности
        # Запрещаем кэширование приватных данных
        if request.path.startswith('/admin/') or request.path.startswith('/directory/'):
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        return response

    def _serve_robots_txt(self):
        """
        Возвращает содержимое robots.txt из static файла.
        """
        # Содержимое robots.txt
        robots_content = """# robots.txt для OT_online
# Защита приватных разделов от индексации поисковыми системами

User-agent: *

# Блокируем админку Django
Disallow: /admin/

# Блокируем все приложение directory (требует авторизации)
Disallow: /directory/

# Блокируем media файлы (содержат приватные данные)
Disallow: /media/

# Блокируем static если содержит чувствительные данные
Disallow: /static/

# Запрещаем любые URL с параметрами (могут содержать токены/ID)
Disallow: /*?*

# Блокируем debug toolbar (если случайно включен)
Disallow: /__debug__/

# Время обхода
Crawl-delay: 10
"""

        response = HttpResponse(robots_content, content_type='text/plain; charset=utf-8')
        response['X-Robots-Tag'] = 'noindex, nofollow'
        return response
