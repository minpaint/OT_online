# 🔐 Руководство по безопасности системы экзаменов

## 📋 Содержание
1. [Архитектура безопасности](#архитектура-безопасности)
2. [Система токенов доступа](#система-токенов-доступа)
3. [Защита от индексации](#защита-от-индексации)
4. [Middleware безопасности](#middleware-безопасности)
5. [Настройка для продакшена](#настройка-для-продакшена)

---

## 🏗️ Архитектура безопасности

### Двухуровневая система доступа

```
┌──────────────────────────────────────────────────────────┐
│  ОСНОВНОЙ ДОМЕН (localhost:8001)                         │
├──────────────────────────────────────────────────────────┤
│  ✅ Полный доступ к системе                              │
│  ✅ Админка Django                                        │
│  ✅ Управление сотрудниками, оборудованием               │
│  ✅ Создание экзаменов и токенов                         │
│  ✅ Просмотр всех данных                                 │
│                                                           │
│  🔒 Защита: стандартная авторизация Django              │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  EXAM ПОДДОМЕН (exam.localhost:8001)                     │
├──────────────────────────────────────────────────────────┤
│  🔐 Изолированный доступ ТОЛЬКО к экзаменам             │
│  ❌ НЕТ доступа к админке                                │
│  ❌ НЕТ доступа к другим данным                          │
│  ✅ ТОЛЬКО экзамены через токены                         │
│                                                           │
│  🔒 Защита: ExamSubdomainMiddleware + токены            │
└──────────────────────────────────────────────────────────┘
```

---

## 🎫 Система токенов доступа

### 1. Создание токена (Администратор)

**Шаг 1:** Зайти в админку основного домена
```
http://localhost:8001/admin/directory/quizaccesstoken/add/
```

**Шаг 2:** Заполнить параметры токена
```python
# Обязательные поля:
- Экзамен: [выбрать из списка]
- Пользователь: [выбрать сотрудника]
- Действителен с: 2025-11-04 10:00:00
- Действителен до: 2025-11-04 18:00:00

# Настройки:
- Требовать авторизацию: ✅ (рекомендуется)
- Разрешить продолжение: ✅ (пользователь может вернуться)
- Максимум попыток: 3
- Описание: "Экзамен по охране труда для Иванова И.И."
```

**Шаг 3:** Сохранить → получить ссылку
```
http://exam.localhost:8001/directory/quiz/access/a1b2c3d4-e5f6-7890-abcd-ef1234567890/
```

**Шаг 4:** Отправить ссылку пользователю

### 2. Использование токена (Сотрудник)

#### Сценарий 1: Первый вход

```
1. Пользователь получает ссылку:
   http://exam.localhost:8001/directory/quiz/access/UUID-токена/

2. Открывает ссылку → Middleware проверяет:
   ✅ Домен = exam.localhost?
   ✅ URL = /directory/quiz/access/*?
   ✅ Токен существует?
   ✅ Токен активен (is_active=True)?
   ✅ Токен в периоде действия (valid_from <= now <= valid_until)?

3. Если требуется авторизация (require_login=True):
   → Перенаправление на страницу входа
   → После входа возврат к токену

4. Проверка прав пользователя:
   ✅ Токен принадлежит этому пользователю?
   ИЛИ
   ✅ Пользователь = суперадмин? (для тестирования)

5. Сохранение в сессии:
   request.session['quiz_token_mode'] = True
   request.session['quiz_token_id'] = token.id

6. Перенаправление на главную страницу экзамена:
   → /directory/quiz/home/
```

#### Сценарий 2: Работа в токен-режиме

```
Пока quiz_token_mode = True в сессии:

✅ РАЗРЕШЕНО:
   /directory/quiz/*           - ВСЕ URL квизов
   /media/*                    - Изображения к вопросам
   /static/*                   - CSS, JS, иконки
   /__debug__/*                - Debug Toolbar (только DEBUG=True)
   /favicon.ico                - Иконка сайта

❌ ЗАБЛОКИРОВАНО:
   /admin/*                    - Админка
   /directory/employees/*      - Сотрудники
   /directory/equipment/*      - Оборудование
   /directory/medical/*        - Медосмотры
   ВСЁ ОСТАЛЬНОЕ               - 403 Forbidden

Логирование:
   Все попытки доступа к запрещённым URL логируются в django.log
```

#### Сценарий 3: Завершение работы

```
Токен-режим остаётся активным:
- До закрытия браузера (сессия)
- До истечения токена (valid_until)
- До logout пользователя

Пользователь может:
- Проходить экзамен несколько раз (в пределах max_attempts)
- Проходить тренировки по разделам
- Возвращаться к экзамену (если allow_resume=True)
```

### 3. Контроль доступа на уровне кода

**View: token_access** (`quiz_views.py:687-754`)
```python
def token_access(request, token):
    """Вход по токену доступа"""

    # 1. Проверка токена в БД
    token_obj = get_object_or_404(QuizAccessToken, token=token)

    # 2. Проверка активности
    if not token_obj.is_active:
        return HttpResponseForbidden("Токен деактивирован")

    # 3. Проверка периода действия
    now = timezone.now()
    if now < token_obj.valid_from or now > token_obj.valid_until:
        return HttpResponseForbidden("Токен истёк")

    # 4. Проверка авторизации
    if token_obj.require_login and not request.user.is_authenticated:
        return redirect(f'/directory/auth/login/?next={request.path}')

    # 5. Проверка владельца
    if request.user != token_obj.user and not request.user.is_superuser:
        return HttpResponseForbidden("Токен не принадлежит вам")

    # 6. Активация токен-режима
    request.session['quiz_token_mode'] = True
    request.session['quiz_token_id'] = token_obj.id

    # 7. Перенаправление на главную
    return redirect('directory:quiz:exam_home')
```

---

## 🚫 Защита от индексации

### 1. robots.txt на exam поддомене

**Автоматическая генерация** (`exam_subdomain.py:44-48`)
```python
if request.path == '/robots.txt':
    return HttpResponse(
        "User-agent: *\nDisallow: /\n",
        content_type="text/plain"
    )
```

**Результат:**
```
http://exam.localhost:8001/robots.txt

User-agent: *
Disallow: /
```

Запрещает индексацию **ВСЕГО** поддомена exam.* любыми поисковиками.

### 2. HTTP-заголовки

**Добавляются ко ВСЕМ ответам** на exam поддомене (`exam_subdomain.py:101-133`):

```python
# Блокировка индексации
response['X-Robots-Tag'] = 'noindex, nofollow, noarchive'

# Content Security Policy (защита от XSS)
response['Content-Security-Policy'] = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
    "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data: https:; "
    "frame-ancestors 'none'; "
    "base-uri 'self';"
)

# Запрет кеширования экзаменов
response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
response['Pragma'] = 'no-cache'
response['Expires'] = '0'

# Защита от clickjacking
response['X-Frame-Options'] = 'DENY'

# Защита от MIME-sniffing
response['X-Content-Type-Options'] = 'nosniff'

# HTTPS только (в продакшене)
if not settings.DEBUG:
    response['Strict-Transport-Security'] = 'max-age=31536000'
```

### 3. Meta-теги в шаблонах

**base_token_mode.html:**
```html
<head>
    <meta name="robots" content="noindex, nofollow, noarchive">
    <meta name="googlebot" content="noindex, nofollow">
    <meta name="yandex" content="noindex, nofollow">
</head>
```

### 4. Логирование попыток доступа

**Все заблокированные запросы логируются:**

```python
[WARNING] 2025-11-04 15:22:32 exam_security:
Exam subdomain access blocked:
IP=192.168.1.100,
Path=/directory/employees/,
Method=GET,
User=ivanov,
Reason=Blocked: not quiz URL in token mode,
User-Agent=Mozilla/5.0 ...
```

**Анализ логов:**
```bash
# Просмотр заблокированных попыток
tail -f django.log | grep "exam_security"

# Статистика по IP
grep "exam_security" django.log | awk '{print $6}' | sort | uniq -c

# Подозрительные попытки (боты)
grep "exam_security" django.log | grep -i "bot\|crawler\|spider"
```

---

## 🛡️ Middleware безопасности

### ExamSubdomainMiddleware

**Файл:** `directory/middleware/exam_subdomain.py`

**Логика работы:**

```python
def __call__(self, request):
    host = request.get_host().lower()

    # 1. Проверка домена
    is_exam_subdomain = (
        host.startswith('exam.') or
        host.startswith('exam:')
    )

    if not is_exam_subdomain:
        # Основной домен - разрешаем всё
        return self.get_response(request)

    # ===== EXAM ПОДДОМЕН =====

    # 2. robots.txt → Disallow: /
    if request.path == '/robots.txt':
        return HttpResponse("User-agent: *\nDisallow: /\n")

    # 3. Debug Toolbar (только DEBUG)
    if request.path.startswith('/__debug__/'):
        if settings.DEBUG:
            return self.get_response(request)
        return HttpResponseForbidden()

    # 4. Статика/медиа → разрешено
    if request.path.startswith('/static/') or request.path.startswith('/media/'):
        return self.get_response(request)

    # 5. Токен-режим активен?
    token_mode = request.session.get('quiz_token_mode', False)

    if token_mode:
        # Разрешены только quiz URL
        if request.path.startswith('/directory/quiz/'):
            return self.get_response(request)
        else:
            # БЛОКИРОВКА + ЛОГИРОВАНИЕ
            self._log_blocked_access(request, "not quiz URL in token mode")
            return HttpResponseForbidden("Access Denied")

    # 6. Без токен-режима - только вход по токену
    allowed = [
        '/directory/quiz/access/',
        '/directory/auth/login/',
        '/accounts/login/',
    ]

    for path in allowed:
        if request.path.startswith(path):
            return self.get_response(request)

    # 7. ВСЁ ОСТАЛЬНОЕ → 403
    self._log_blocked_access(request, "no token mode")
    return HttpResponseForbidden("Access Denied")
```

---

## 🚀 Настройка для продакшена

### 1. Nginx конфигурация

**Файл:** `/etc/nginx/sites-available/ot_online`

```nginx
# Основной домен
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/ot_online/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/ot_online/media/;
        expires 7d;
    }
}

# EXAM поддомен (изолированный)
server {
    listen 80;
    server_name exam.yourdomain.com;

    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name exam.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Дополнительные заголовки безопасности
    add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer" always;

    # Запрет на индексацию
    location = /robots.txt {
        add_header Content-Type text/plain;
        return 200 "User-agent: *\nDisallow: /\n";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /var/www/ot_online/staticfiles/;
        expires 7d;  # Меньше кеш для exam
    }

    location /media/ {
        alias /var/www/ot_online/media/;
        expires 1d;  # Минимальный кеш для изображений вопросов
    }
}
```

### 2. Django settings (продакшен)

**settings.py:**
```python
# Домены
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'exam.yourdomain.com']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Exam поддомен
EXAM_SUBDOMAIN = 'exam.yourdomain.com'
EXAM_PROTOCOL = 'https'

# Security headers (дополнительно к middleware)
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
```

### 3. Переменные окружения (.env)

```env
# Продакшен
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,exam.yourdomain.com

# Exam поддомен
EXAM_SUBDOMAIN=exam.yourdomain.com
EXAM_PROTOCOL=https

# База данных
DATABASE_URL=postgresql://user:password@localhost:5432/ot_online

# Email для уведомлений о безопасности
SECURITY_EMAIL=admin@yourdomain.com
```

### 4. SSL сертификаты (Let's Encrypt)

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата для обоих доменов
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d exam.yourdomain.com

# Автопродление
sudo certbot renew --dry-run
```

### 5. Мониторинг безопасности

**Настройка логирования:**

```python
# settings.py
LOGGING = {
    'version': 1,
    'handlers': {
        'file_exam_security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/ot_online/exam_security.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
        },
    },
    'loggers': {
        'exam_security': {
            'handlers': ['file_exam_security'],
            'level': 'WARNING',
        },
    },
}
```

**Мониторинг с помощью fail2ban:**

```bash
# /etc/fail2ban/filter.d/exam-access.conf
[Definition]
failregex = Exam subdomain access blocked: IP=<HOST>
ignoreregex =

# /etc/fail2ban/jail.local
[exam-access]
enabled = true
port = http,https
filter = exam-access
logpath = /var/log/ot_online/exam_security.log
maxretry = 10
bantime = 3600
findtime = 600
```

**Email уведомления:**

```python
# При подозрительной активности
if suspicious_activity_detected:
    from django.core.mail import send_mail

    send_mail(
        'SECURITY: Подозрительная активность на exam поддомене',
        f'IP: {ip}\nПопыток: {count}\nURL: {blocked_urls}',
        'noreply@yourdomain.com',
        ['admin@yourdomain.com'],
        fail_silently=False,
    )
```

---

## 📊 Проверка безопасности

### Чек-лист перед запуском в продакшен:

```
✅ SSL сертификаты настроены для обоих доменов
✅ ALLOWED_HOSTS содержит оба домена
✅ DEBUG=False
✅ SECURE_SSL_REDIRECT=True
✅ SESSION_COOKIE_SECURE=True
✅ CSRF_COOKIE_SECURE=True
✅ ExamSubdomainMiddleware в MIDDLEWARE
✅ robots.txt на exam.* возвращает Disallow: /
✅ Nginx добавляет заголовки безопасности
✅ Логирование настроено
✅ Мониторинг работает
✅ Email уведомления работают
```

### Тестирование:

**1. Проверка robots.txt:**
```bash
curl https://exam.yourdomain.com/robots.txt

# Ожидаемый результат:
User-agent: *
Disallow: /
```

**2. Проверка заголовков:**
```bash
curl -I https://exam.yourdomain.com/

# Ожидаемые заголовки:
X-Robots-Tag: noindex, nofollow, noarchive
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Strict-Transport-Security: max-age=31536000
```

**3. Проверка доступа без токена:**
```bash
curl https://exam.yourdomain.com/directory/employees/

# Ожидаемый результат: 403 Forbidden
```

**4. Проверка Google Search Console:**
- Добавить exam.yourdomain.com
- Убедиться, что индексация заблокирована
- Запросить исключение из индекса (если уже было проиндексировано)

---

## 🆘 FAQ по безопасности

**Q: Может ли пользователь обойти токен-режим?**
A: Нет. Middleware проверяет КАЖДЫЙ запрос на уровне HTTP. Даже если пользователь знает URL, без токена в сессии доступ будет заблокирован.

**Q: Что если токен утёк третьим лицам?**
A: Токен можно деактивировать в админке (is_active=False). Также есть период действия (valid_until).

**Q: Индексирует ли Google exam поддомен?**
A: Нет, если:
- robots.txt настроен
- X-Robots-Tag добавлен
- Meta-теги в шаблонах
Всё это уже реализовано.

**Q: Можно ли использовать один токен для нескольких пользователей?**
A: Нет, токен привязан к конкретному пользователю (user FK). Администратор может создать несколько токенов для одного экзамена.

**Q: Что если пользователь не закрыл браузер после экзамена?**
A: Токен-режим остаётся активным, но:
- Доступ только к quiz URL
- Доступ к админке/другим данным заблокирован
- После истечения токена (valid_until) доступ прекращается

**Q: Логируются ли просмотры вопросов экзамена?**
A: Да, можно добавить дополнительное логирование. Сейчас логируются:
- Начало попытки (QuizAttempt)
- Каждый ответ (UserAnswer)
- Заблокированные запросы (exam_security.log)

---

## 📞 Поддержка

При возникновении проблем с безопасностью:
1. Проверьте логи: `tail -f /var/log/ot_online/exam_security.log`
2. Проверьте настройки Django: `python manage.py check --deploy`
3. Проверьте Nginx: `sudo nginx -t`
4. Свяжитесь с администратором системы
