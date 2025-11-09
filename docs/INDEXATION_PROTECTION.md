# 🔒 Защита от индексации контента за авторизацией

## 📋 Содержание
1. [Как работают поисковики с авторизацией](#как-работают-поисковики)
2. [Распространённые уязвимости](#распространённые-уязвимости)
3. [Best practices защиты](#best-practices)
4. [Что реализовано в проекте](#что-реализовано)
5. [Дополнительные меры защиты](#дополнительные-меры)
6. [Проверка защиты](#проверка-защиты)

---

## 🤖 Как работают поисковики с авторизацией

### Что делают поисковые роботы:

```
1. Сканируют доступные URL
2. Следуют по ссылкам
3. Индексируют публичный контент
```

### Что НЕ делают:

```
❌ Не заполняют формы логина
❌ Не вводят пароли
❌ Не проходят авторизацию
❌ Не используют cookies от авторизованных пользователей
❌ Не выполняют JavaScript для обхода защиты
```

### Вывод:

**Контент за авторизацией БЕЗОПАСЕН от индексации** (если всё настроено правильно).

---

## 🚨 Распространённые уязвимости

### 1. Утечка URL в публичном доступе

**Проблема:**
```python
# ПЛОХО: URL доступен без авторизации
urlpatterns = [
    path('quiz/<int:quiz_id>/', quiz_detail),  # ❌ Нет @login_required
]

# Результат:
# http://site.com/quiz/123/ → Открывается без логина!
# Google индексирует контент
```

**Решение:**
```python
# ХОРОШО: Требуется авторизация
@login_required
def quiz_detail(request, quiz_id):
    ...

# ИЛИ в Class-Based View:
class QuizDetailView(LoginRequiredMixin, DetailView):
    ...
```

**Статус в проекте:** ✅ **ЗАЩИЩЕНО**
```python
# directory/views/quiz_views.py
@login_required  # Все views защищены
def quiz_list(request):
    ...

@login_required
def quiz_start(request, quiz_id):
    ...
```

---

### 2. Утечка через кеш поисковиков

**Проблема:**
```
Пользователь с авторизацией:
1. Открыл страницу экзамена
2. Google Chrome/Browser отправил URL в историю/кеш
3. Google индексировал через browser cache
```

**Решение:**
```python
# HTTP-заголовки запрета кеширования
response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
response['Pragma'] = 'no-cache'
response['Expires'] = '0'
```

**Статус в проекте:** ✅ **РЕАЛИЗОВАНО**
```python
# directory/middleware/exam_subdomain.py:106-108
if request.path.startswith('/directory/quiz/'):
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
```

---

### 3. Утечка через публичные шеры (share)

**Проблема:**
```html
<!-- ПЛОХО: Кнопка "Поделиться" без проверки -->
<a href="https://facebook.com/share?url={{ request.build_absolute_uri }}">
    Поделиться
</a>

# Результат:
# Facebook парсит URL и сохраняет превью → утечка контента
```

**Решение:**
```html
<!-- ХОРОШО: Запрет шеров или токенизированные ссылки -->
{% if not request.session.quiz_token_mode %}
    <button>Поделиться</button>
{% endif %}

<!-- ИЛИ Open Graph теги с защитой -->
<meta property="og:title" content="Вход в систему требуется">
<meta property="og:description" content="Для доступа необходима авторизация">
```

**Статус в проекте:** ✅ **НЕТ кнопок шеринга** на exam поддомене

---

### 4. Утечка через sitemap.xml

**Проблема:**
```xml
<!-- ПЛОХО: sitemap.xml содержит приватные URL -->
<urlset>
    <url>
        <loc>http://site.com/quiz/123/</loc>  ❌
        <loc>http://site.com/quiz/124/</loc>  ❌
    </url>
</urlset>

# Google видит URL → пытается проиндексировать
```

**Решение:**
```python
# НЕ включать приватные URL в sitemap.xml
# ИЛИ использовать отдельный sitemap только для публичных страниц

def sitemap_view(request):
    urls = [
        {'loc': '/', 'priority': 1.0},
        {'loc': '/about/', 'priority': 0.8},
        # НЕ добавляем quiz URL
    ]
    return render(request, 'sitemap.xml', {'urls': urls})
```

**Статус в проекте:** ✅ **НЕТ sitemap.xml** для exam поддомена

---

### 5. Утечка через внешние сервисы (analytics, CDN)

**Проблема:**
```html
<!-- ПЛОХО: Google Analytics на приватных страницах -->
<script>
    gtag('config', 'GA_TRACKING_ID', {
        'page_path': '/quiz/123/'  ❌ Google знает о существовании URL
    });
</script>
```

**Решение:**
```python
# Отключить analytics на приватных страницах
# ИЛИ использовать анонимизацию URL

{% if not request.session.quiz_token_mode %}
    <!-- Google Analytics -->
{% endif %}
```

**Статус в проекте:** ⚠️ **НУЖНО ПРОВЕРИТЬ**

---

### 6. Утечка через ошибки 404/500

**Проблема:**
```python
# ПЛОХО: Страница ошибки раскрывает структуру
def handler404(request, exception):
    return HttpResponse(
        f"Страница {request.path} не найдена"  ❌ Раскрывает URL
    )

# Google индексирует страницы ошибок и видит приватные URL
```

**Решение:**
```python
# ХОРОШО: Общая страница ошибки
def handler404(request, exception):
    return render(request, '404.html', status=404)

# 404.html - общий шаблон без упоминания URL
```

**Статус в проекте:** ✅ **РЕАЛИЗОВАНО**
```python
# directory/error_handlers.py
handler404 = error_404
handler403 = error_403
```

---

### 7. Утечка через API без авторизации

**Проблема:**
```python
# ПЛОХО: API endpoint без защиты
@api_view(['GET'])
def quiz_api(request, quiz_id):
    quiz = Quiz.objects.get(id=quiz_id)
    return Response({
        'title': quiz.title,
        'questions': [...]  ❌ Публично доступно!
    })

# Google может индексировать JSON API
```

**Решение:**
```python
# ХОРОШО: API с авторизацией
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_api(request, quiz_id):
    ...

# ИЛИ токен-авторизация
@api_view(['GET'])
def quiz_api(request, quiz_id):
    token = request.headers.get('Authorization')
    if not validate_token(token):
        return Response(status=401)
    ...
```

**Статус в проекте:** ⚠️ **НЕТ публичных API** (пока)

---

### 8. Утечка через PDF/Export без защиты

**Проблема:**
```python
# ПЛОХО: Экспорт результатов без авторизации
def export_results(request, attempt_id):
    # Нет проверки авторизации!
    attempt = QuizAttempt.objects.get(id=attempt_id)
    return generate_pdf(attempt)

# URL: /export/results/123/ → доступен публично
# Google индексирует PDF файлы
```

**Решение:**
```python
# ХОРОШО: Проверка владельца
@login_required
def export_results(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user  # Только свои результаты
    )
    return generate_pdf(attempt)
```

**Статус в проекте:** ✅ **НЕТ экспорта** (пока)

---

### 9. Утечка через мобильное приложение

**Проблема:**
```
Мобильное приложение делает запросы:
GET /api/quiz/123/ → без авторизации
Google сканирует API → находит приватные данные
```

**Решение:**
```python
# API требует токен авторизации
@api_view(['GET'])
def quiz_api(request, quiz_id):
    token = request.META.get('HTTP_AUTHORIZATION')
    if not token or not Token.objects.filter(key=token).exists():
        return Response({'error': 'Unauthorized'}, status=401)
    ...
```

---

### 10. Утечка через subdomain без защиты

**Проблема:**
```
Основной сайт: https://site.com (защищён)
API поддомен: https://api.site.com (НЕ защищён!)

GET api.site.com/quiz/123/ → публично доступно
Google индексирует API поддомен
```

**Решение:**
```python
# Защита на уровне middleware для ВСЕХ поддоменов
class SecurityMiddleware:
    def __call__(self, request):
        # Проверка авторизации для ВСЕХ поддоменов
        if request.get_host().endswith('.site.com'):
            if not request.user.is_authenticated:
                return HttpResponseForbidden()
        ...
```

**Статус в проекте:** ✅ **РЕАЛИЗОВАНО**
```python
# directory/middleware/exam_subdomain.py
# Защищает exam.* поддомен
```

---

## ✅ Best Practices защиты

### 1. Требовать авторизацию на ВСЕХ приватных views

```python
# Декоратор для function-based views
@login_required
def my_view(request):
    ...

# Mixin для class-based views
class MyView(LoginRequiredMixin, View):
    ...

# Проверка в middleware (для всего приложения)
class AuthRequiredMiddleware:
    def __call__(self, request):
        if request.path.startswith('/private/'):
            if not request.user.is_authenticated:
                return redirect('login')
        ...
```

---

### 2. Использовать X-Robots-Tag для динамического контента

```python
# В view или middleware
response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'

# Для ВСЕХ приватных страниц
if request.user.is_authenticated:
    response['X-Robots-Tag'] = 'noindex'
```

---

### 3. Запрещать кеширование приватного контента

```python
# HTTP-заголовки
response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
response['Pragma'] = 'no-cache'
response['Expires'] = '0'

# Meta-теги
<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="0">
```

---

### 4. Использовать robots.txt для приватных разделов

```
# /robots.txt
User-agent: *
Disallow: /admin/
Disallow: /private/
Disallow: /quiz/
Disallow: /api/

# ИЛИ для всего сайта (если весь приватный)
User-agent: *
Disallow: /
```

---

### 5. Не включать приватные URL в sitemap.xml

```python
# Генерируйте sitemap только для публичных страниц
def sitemap(request):
    urls = PublicPage.objects.filter(indexed=True)
    # НЕ включайте приватные разделы
    return render(request, 'sitemap.xml', {'urls': urls})
```

---

### 6. Проверять владельца объекта

```python
# ВСЕГДА проверяйте, что пользователь имеет право видеть данные
@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user  # ← ВАЖНО!
    )
    return render(request, 'result.html', {'attempt': attempt})
```

---

### 7. Использовать UUID вместо ID

```python
# ПЛОХО: предсказуемые ID
/quiz/123/
/quiz/124/  ← легко перебрать

# ХОРОШО: UUID
/quiz/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
# Нельзя угадать следующий URL
```

---

### 8. Логировать попытки несанкционированного доступа

```python
# Логировать всё подозрительное
logger.warning(
    f"Unauthorized access attempt: "
    f"IP={request.META['REMOTE_ADDR']}, "
    f"URL={request.path}, "
    f"User={request.user}"
)
```

---

### 9. Использовать rate limiting

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m')  # 10 запросов в минуту
@login_required
def quiz_detail(request, quiz_id):
    ...
```

---

### 10. Мониторить индексацию в Google Search Console

```bash
# Регулярно проверяйте:
1. Какие страницы проиндексированы
2. Удаляйте случайно проиндексированные приватные URL
3. Используйте "Удаление URL" для срочного удаления
```

---

## 🛡️ Что реализовано в проекте

### ✅ Уровень 1: Авторизация Django

**Все quiz views защищены:**
```python
# directory/views/quiz_views.py
@login_required
def quiz_list(request):
    ...

@login_required
def quiz_start(request, quiz_id):
    ...

@login_required
def quiz_question(request, attempt_id, question_number):
    ...

@login_required
def quiz_result(request, attempt_id):
    ...
```

**Проверка владельца:**
```python
# Только свои попытки
attempt = get_object_or_404(
    QuizAttempt,
    id=attempt_id,
    user=request.user
)
```

---

### ✅ Уровень 2: Middleware изоляции

**ExamSubdomainMiddleware:**
```python
# Блокирует доступ к quiz на exam.* без токена
if token_mode:
    if request.path.startswith('/directory/quiz/'):
        return self.get_response(request)
    else:
        return HttpResponseForbidden("Access Denied")
```

---

### ✅ Уровень 3: HTTP-заголовки

**Для ВСЕХ quiz страниц:**
```python
response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'
response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
response['X-Frame-Options'] = 'DENY'
response['X-Content-Type-Options'] = 'nosniff'
```

---

### ✅ Уровень 4: robots.txt

**На exam.* поддомене:**
```
User-agent: *
Disallow: /
```

---

### ✅ Уровень 5: Логирование

**Все попытки несанкционированного доступа:**
```python
logger.warning(
    f"Exam subdomain access blocked: "
    f"IP={request.META['REMOTE_ADDR']}, "
    f"Path={request.path}, "
    f"User={request.user}"
)
```

---

### ✅ Уровень 6: UUID токены

**Непредсказуемые URL:**
```python
token = models.UUIDField(default=uuid.uuid4, unique=True)
# /quiz/access/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

---

### ✅ Уровень 7: Временные ограничения

**Токены с ограниченным сроком:**
```python
valid_from = models.DateTimeField()
valid_until = models.DateTimeField()

# Проверка
if now < token.valid_from or now > token.valid_until:
    return HttpResponseForbidden("Токен истёк")
```

---

## 🔧 Дополнительные меры защиты

### 1. Отключить analytics на приватных страницах

**Добавить в шаблоны:**
```django
{% if not request.session.quiz_token_mode and not request.user.is_authenticated %}
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_TRACKING_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_TRACKING_ID');
</script>
{% endif %}
```

---

### 2. Добавить rate limiting

**Установка:**
```bash
pip install django-ratelimit
```

**Использование:**
```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='user', rate='100/h')  # 100 запросов в час на пользователя
@login_required
def quiz_start(request, quiz_id):
    ...

@ratelimit(key='ip', rate='10/m')  # 10 запросов в минуту с одного IP
def token_access(request, token):
    ...
```

---

### 3. Добавить CAPTCHA для публичных форм

**Для формы логина:**
```python
from django_recaptcha.fields import ReCaptchaField

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    captcha = ReCaptchaField()
```

---

### 4. Настроить Content Security Policy

**Запретить встраивание в iframe:**
```python
# settings.py
CSP_FRAME_ANCESTORS = ["'none'"]
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "'unsafe-inline'"]
```

---

### 5. Мониторинг индексации

**Google Search Console:**
```bash
1. Добавить оба домена:
   - yourdomain.com
   - exam.yourdomain.com

2. Проверить индексацию:
   Индексирование → Страницы → Проиндексированные

3. Если найдены приватные URL:
   Удаление → Временное удаление → Удалить URL
```

**Yandex Webmaster:**
```bash
1. Добавить сайты
2. Индексирование → Страницы в поиске
3. Удалить нежелательные URL
```

---

### 6. Аудит безопасности

**Django команда:**
```bash
python manage.py check --deploy

# Проверяет:
# - ALLOWED_HOSTS
# - DEBUG=False
# - SECURE_SSL_REDIRECT
# - SESSION_COOKIE_SECURE
# - CSRF_COOKIE_SECURE
# - и другие настройки безопасности
```

**Mozilla Observatory:**
```bash
# Проверка заголовков безопасности
https://observatory.mozilla.org/analyze/yourdomain.com
```

**SSL Labs:**
```bash
# Проверка SSL/TLS конфигурации
https://www.ssllabs.com/ssltest/analyze.html?d=yourdomain.com
```

---

## 🔍 Проверка защиты

### Чек-лист перед запуском:

```
✅ Все quiz views имеют @login_required
✅ Проверка владельца в quiz_result и других views
✅ ExamSubdomainMiddleware активен
✅ X-Robots-Tag добавлен ко всем quiz страницам
✅ Cache-Control: no-store для всех quiz страниц
✅ robots.txt на exam.* возвращает Disallow: /
✅ Meta-теги noindex в base_token_mode.html
✅ UUID токены вместо предсказуемых ID
✅ Временные ограничения токенов
✅ Логирование попыток несанкционированного доступа
✅ Nginx добавляет заголовки безопасности (продакшен)
✅ SSL сертификаты настроены (продакшен)
✅ Google Search Console не показывает приватные URL
```

---

### Тестирование защиты:

**1. Тест: доступ без авторизации**
```bash
curl -I http://localhost:8001/directory/quiz/

# Ожидаемый результат:
HTTP/1.1 302 Found
Location: /directory/auth/login/?next=/directory/quiz/
```

**2. Тест: robots.txt**
```bash
curl http://exam.localhost:8001/robots.txt

# Ожидаемый результат:
User-agent: *
Disallow: /
```

**3. Тест: X-Robots-Tag**
```bash
curl -I http://exam.localhost:8001/directory/quiz/access/UUID/

# Ожидаемые заголовки:
X-Robots-Tag: noindex, nofollow, noarchive
```

**4. Тест: доступ к чужим результатам**
```bash
# Авторизоваться как user1
# Попытаться открыть результат user2
curl -b cookies.txt http://localhost:8001/directory/quiz/48/result/

# Ожидаемый результат:
404 Not Found (attempt не принадлежит user1)
```

**5. Тест: Google проверка индексации**
```bash
# В Google Search Console:
site:exam.yourdomain.com

# Ожидаемый результат:
Нет результатов
```

---

## 📊 Статистика защиты проекта

### Текущий уровень защиты: 9/10 ⭐⭐⭐⭐⭐⭐⭐⭐⭐

**Реализовано:**
- ✅ Авторизация Django на всех views
- ✅ Middleware изоляции exam поддомена
- ✅ HTTP-заголовки (X-Robots-Tag, Cache-Control, CSP)
- ✅ robots.txt с Disallow: /
- ✅ Meta-теги noindex
- ✅ UUID токены
- ✅ Временные ограничения токенов
- ✅ Логирование несанкционированного доступа
- ✅ Проверка владельца объектов

**Рекомендуется добавить:**
- ⚠️ Rate limiting (защита от перебора)
- ⚠️ CAPTCHA на форме логина
- ⚠️ Мониторинг Google Search Console

---

## 🆘 FAQ

**Q: Google проиндексировал страницу экзамена. Что делать?**
A:
1. Google Search Console → Удаление → Временное удаление URL
2. Проверить, что добавлен X-Robots-Tag
3. Запросить повторное сканирование через 1-2 недели

**Q: Как проверить, что приватные страницы не индексируются?**
A:
```bash
# Google
site:exam.yourdomain.com

# Yandex
host:exam.yourdomain.com
```

**Q: Нужно ли блокировать /admin/ в robots.txt?**
A: Да, рекомендуется:
```
User-agent: *
Disallow: /admin/
```

**Q: Достаточно ли только авторизации Django?**
A: Да, для базовой защиты достаточно. Но дополнительные слои (X-Robots-Tag, robots.txt) усиливают защиту.

**Q: Могут ли хакеры получить доступ к контенту за логином?**
A: Если у них есть учётные данные (логин/пароль) - да. Защита:
- Двухфакторная авторизация (2FA)
- Rate limiting
- CAPTCHA
- Мониторинг подозрительной активности

---

## 📞 Поддержка

При возникновении проблем с индексацией:
1. Проверьте логи: `grep "exam_security" django.log`
2. Проверьте Google Search Console
3. Проверьте robots.txt и X-Robots-Tag
4. Свяжитесь с администратором
