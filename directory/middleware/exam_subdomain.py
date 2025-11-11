# directory/middleware/exam_subdomain.py
import logging
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings

logger = logging.getLogger('exam_security')


class ExamSubdomainMiddleware:
    """
    Middleware для строгой изоляции exam.* поддомена

    Функции:
    1. Блокирует индексацию поисковыми системами (robots.txt, заголовки)
    2. Разрешает доступ ТОЛЬКО через валидные токены
    3. Без токена - возвращает 403 Forbidden
    4. Добавляет заголовки безопасности (CSP, X-Robots-Tag, Cache-Control)
    5. Логирует все попытки несанкционированного доступа
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()

        # Проверяем, это exam.* поддомен?
        # Поддерживаем различные форматы: exam.domain.com, exam.localhost:8001
        is_exam_subdomain = (
            host.startswith('exam.') or
            host.startswith('exam:')  # для локальной разработки
        )

        if not is_exam_subdomain:
            # Основной домен - пропускаем без изменений
            return self.get_response(request)

        # ====== ЭТО EXAM.* ПОДДОМЕН ======

        # Помечаем запрос как идущий с exam поддомена
        request.is_exam_subdomain = True

        # 1. ROBOTS.TXT - всегда запрещаем индексацию
        if request.path == '/robots.txt':
            return HttpResponse(
                "User-agent: *\nDisallow: /\n",
                content_type="text/plain"
            )

        # 2. Django Debug Toolbar и favicon - разрешаем в режиме разработки
        if request.path.startswith('/__debug__/') or request.path == '/favicon.ico':
            # В DEBUG режиме разрешаем доступ к debug toolbar
            from django.conf import settings
            if settings.DEBUG:
                return self.get_response(request)
            # В продакшене блокируем
            return HttpResponseForbidden("Access Denied")

        # 3. Статические и медиа файлы - разрешаем БЕЗ CSP заголовков
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            logger.info(f"Exam subdomain: serving media/static file: {request.path}")
            response = self.get_response(request)
            # Для статики/медиа добавляем только базовые заголовки безопасности
            response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
            response['X-Content-Type-Options'] = 'nosniff'
            # НЕ добавляем CSP для изображений - это может блокировать их отображение
            return response

        # 4. Проверяем токен-режим в сессии
        token_mode = request.session.get('quiz_token_mode', False)

        # Список разрешённых путей БЕЗ токен-режима
        allowed_without_token = [
            '/directory/quiz/access/',    # Вход по токену
            '/directory/auth/login/',     # Страница авторизации (Django app)
            '/directory/auth/logout/',    # Выход (Django app)
            '/accounts/login/',           # Страница авторизации (резервный путь)
            '/accounts/logout/',          # Выход (резервный путь)
        ]

        # 5. Если токен-режим активен - разрешаем только quiz URL
        if token_mode:
            if request.path.startswith('/directory/quiz/'):
                response = self.get_response(request)
                return self._add_security_headers(request, response)
            else:
                # Попытка доступа к запрещённому URL в токен-режиме
                self._log_blocked_access(request, "Blocked: not quiz URL in token mode")
                return HttpResponseForbidden("Access Denied")

        # 6. Без токен-режима - проверяем разрешённые пути
        for allowed_path in allowed_without_token:
            if request.path.startswith(allowed_path):
                response = self.get_response(request)
                return self._add_security_headers(request, response)

        # 7. ВСЁ ОСТАЛЬНОЕ - блокируем
        self._log_blocked_access(request, "Blocked: no token mode")
        return HttpResponseForbidden("Access Denied")

    def _add_security_headers(self, request, response):
        """Добавляем заголовки безопасности"""

        # Блокируем индексацию поисковыми системами
        response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'

        # Content Security Policy - защита от XSS и injection атак
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://code.jquery.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self' https://cdn.jsdelivr.net https://code.jquery.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self';"
        )

        # Запрещаем кеширование чувствительных страниц
        if request.path.startswith('/directory/quiz/'):
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'

        # Защита от clickjacking
        response['X-Frame-Options'] = 'DENY'

        # Защита от MIME-type sniffing
        response['X-Content-Type-Options'] = 'nosniff'

        # Включаем HTTPS (в продакшене)
        if not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    def _log_blocked_access(self, request, reason):
        """Логирование заблокированных попыток доступа"""
        logger.warning(
            f"Exam subdomain access blocked: "
            f"IP={request.META.get('REMOTE_ADDR', 'unknown')}, "
            f"Path={request.path}, "
            f"Method={request.method}, "
            f"User={request.user if request.user.is_authenticated else 'Anonymous'}, "
            f"Reason={reason}, "
            f"User-Agent={request.META.get('HTTP_USER_AGENT', 'unknown')[:100]}"
        )
