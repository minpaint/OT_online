import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages
import warnings

# 📌 Подавление предупреждений о pkg_resources от docxcompose
warnings.filterwarnings('ignore', message='.*pkg_resources is deprecated.*')

# 📌 Загрузка переменных окружения из файла .env
load_dotenv()

# 📂 Определяем корневой каталог проекта
BASE_DIR = Path(__file__).resolve().parent

# 🧪 Определяем, запущены ли тесты
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# 🔐 Основные настройки безопасности
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True' and not TESTING
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', 'pot.by,www.pot.by,192.168.37.10,127.0.0.1,localhost').split(',')
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


# 📱 Базовые приложения  ────────────────────────────────────────────────
DJANGO_APPS = [
    'config.apps.OTAdminConfig', # Замена меню в админке Django 👨‍💼
    'django.contrib.auth',       # Аутентификация 🔑
    'django.contrib.contenttypes', # Типы контента 📄
    'django.contrib.sessions',   # Сессии пользователя 🕑
    'django.contrib.messages',   # Сообщения 📨
    'django.contrib.staticfiles', # Статические файлы 🖼️
]

# 🔌 Сторонние приложения
THIRD_PARTY_APPS = [
    'corsheaders',              # CORS настройки 🌐
    'django_extensions',        # Расширения Django ⚙️
    'dal',                     # Django Autocomplete Light 🔍
    'dal_select2',            # Виджеты Select2 для DAL 🎯
    'crispy_forms',           # Красивые формы ✨
    'crispy_bootstrap4',      # Bootstrap 4 для crispy-forms 🎨
    'import_export',          # Для импорта/экспорта данных
    'nested_admin',           # Для вложенных админ-интерфейсов
]

# 🏠 Локальные приложения
LOCAL_APPS = [
    'directory.apps.DirectoryConfig',  # Наше приложение "directory" 📦
    'deadline_control',  # Контроль сроков ⏰
]

# Добавляем debug_toolbar только если не в режиме тестирования и DEBUG=True
if not TESTING and DEBUG:
    THIRD_PARTY_APPS.append('debug_toolbar')

# Объединяем все приложения
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# 🛠️ Базовый middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',     # Защита 🔒
    'whitenoise.middleware.WhiteNoiseMiddleware',        # WhiteNoise для статики 🎨
    'django.contrib.sessions.middleware.SessionMiddleware', # Сессии 🕑
    'corsheaders.middleware.CorsMiddleware',            # CORS 🌐
    'django.middleware.common.CommonMiddleware',         # Общие настройки 🔧
    'django.middleware.csrf.CsrfViewMiddleware',        # CSRF защита 🚫
    'django.contrib.auth.middleware.AuthenticationMiddleware', # Аутентификация 🔑
    'directory.middleware.AccessCacheMiddleware',        # Request-level кеш прав доступа 🔐
    'django.contrib.messages.middleware.MessageMiddleware', # Сообщения 📨
    'django.middleware.clickjacking.XFrameOptionsMiddleware', # Защита от clickjacking 🖱️
    'directory.middleware.ExamSubdomainMiddleware',      # Изоляция exam.* поддомена 🔐
    'directory.middleware.anti_indexation.AntiIndexationMiddleware',  # Защита от индексации 🚫🔍
]

# Добавляем debug_toolbar middleware только если не в режиме тестирования и DEBUG=True
if not TESTING and DEBUG:
    # Вставляем в начало, чтобы обрабатывать запросы раньше
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# 🌐 URL-конфигурация
ROOT_URLCONF = 'urls'

# 📄 Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
            BASE_DIR / 'directory' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media', # Добавлен процессор для MEDIA_URL
                'deadline_control.context_processors.notifications.deadline_notifications', # Уведомления о сроках
            ],
        },
    },
]

# 🌍 WSGI-приложение
WSGI_APPLICATION = 'wsgi.application'

# 💾 База данных
# Определение БД в зависимости от переменной окружения DATABASE_URL
if os.getenv('DATABASE_URL'):
    # Используем dj-database-url для парсинга URL базы данных (удобно для Heroku/Render)
    import dj_database_url
    db_config = dj_database_url.config()
    db_config['CONN_MAX_AGE'] = 600
    if os.getenv('DATABASE_SSL_REQUIRE', 'False') == 'True':
        db_config['OPTIONS'] = {'sslmode': 'require'}
    DATABASES = {'default': db_config}
elif os.getenv('DB_ENGINE'): # Альтернативный способ конфигурации через отдельные переменные
     DATABASES = {
        'default': {
            'ENGINE': os.getenv('DB_ENGINE'),
            'NAME': os.getenv('DB_NAME'),
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
        }
    }
else: # Фолбэк на SQLite для локальной разработки, если ничего не задано
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'TEST': {
                'NAME': BASE_DIR / 'test_db.sqlite3', # Отдельная БД для тестов
            },
        }
    }

# 🔒 Валидаторы паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🌍 Интернационализация
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru-ru')
TIME_ZONE = os.getenv('TIME_ZONE', 'Europe/Moscow')
USE_I18N = True
USE_TZ = True # Рекомендуется использовать True для работы с часовыми поясами

# 📁 Статические файлы - ИСПРАВЛЕНО ДЛЯ СЕРВЕРА
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'directory' / 'static', # Статика из конкретного приложения 'directory'
]
# ИСПРАВЛЕНО: путь для сбора статики на сервере
STATIC_ROOT = BASE_DIR.parent / 'data' / 'static'  # Теперь указывает на /home/django/webapps/soutby/data/static

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# ИСПРАВЛЕНО: используем WhiteNoise для статики
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 📸 Медиа файлы
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media' # Директория для загружаемых пользователем файлов

# 🔑 Тип первичного ключа
DEFAULT_AUTO_FIELD = os.getenv('DEFAULT_AUTO_FIELD', 'django.db.models.BigAutoField')

# 🔗 CORS настройки
# Для разработки можно True, в production лучше указать конкретные домены
CORS_ORIGIN_ALLOW_ALL = os.getenv('CORS_ORIGIN_ALLOW_ALL', 'True') == 'True'
CORS_ALLOW_CREDENTIALS = True
if not CORS_ORIGIN_ALLOW_ALL:
    CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
    CORS_ALLOWED_ORIGIN_REGEXES = os.getenv('CORS_ALLOWED_ORIGIN_REGEXES', '').split(',') # Если нужны регулярные выражения

# 🔐 Настройки аутентификации
LOGIN_URL = 'directory:auth:login' # Убедитесь, что URL 'directory:auth:login' существует
LOGIN_REDIRECT_URL = 'home' # Редирект на главную страницу (корень сайта)
LOGOUT_REDIRECT_URL = 'directory:auth:login'
AUTH_USER_MODEL = 'auth.User' # Стандартная модель пользователя Django

# 🍪 Настройки сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.db' # Хранение сессий в БД
SESSION_COOKIE_AGE = int(os.getenv('SESSION_COOKIE_AGE', 60 * 60 * 24 * 7)) # Время жизни сессии (по умолчанию 1 неделя)
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'False') == 'True' # В production должно быть True (требует HTTPS)
SESSION_EXPIRE_AT_BROWSER_CLOSE = os.getenv('SESSION_EXPIRE_AT_BROWSER_CLOSE', 'False') == 'True' # Удалять ли сессию при закрытии браузера
SESSION_SAVE_EVERY_REQUEST = os.getenv('SESSION_SAVE_EVERY_REQUEST', 'False') == 'True' # Обновлять сессию при каждом запросе

# 🔒 CSRF настройки
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', 'False') == 'True' # В production должно быть True (требует HTTPS)
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8000,http://127.0.0.1:8000').split(',')

# 🎨 Настройки форм Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = ('bootstrap4',)
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_FAIL_SILENTLY = not DEBUG # Не показывать ошибки crispy в production

# 💬 Настройки сообщений Django Messages Framework
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage' # Хранить сообщения в сессии
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# 🌐 Настройки для Select2 (если используются статические файлы)
# Пути относительно STATIC_URL, убедитесь, что файлы есть в STATICFILES_DIRS или приложениях
SELECT2_JS = 'vendor/select2/dist/js/select2.min.js'
SELECT2_CSS = 'vendor/select2/dist/css/select2.min.css'
SELECT2_I18N_PATH = 'vendor/select2/dist/js/i18n'

# 🔍 Настройки для django-autocomplete-light
DAL_MAX_RESULTS = 10 # Максимальное количество результатов в автодополнении
DAL_FORWARD_FIELDS = True # Разрешить передачу полей с формы в виджет
DAL_DELETE_ON_AJAX = True # Разрешить удаление связанных объектов через AJAX (используйте с осторожностью)

# 📧 Email настройки
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend') # По умолчанию вывод в консоль
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True' # Обычно TLS или SSL, не оба
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'webmaster@localhost') # Email отправителя по умолчанию
SERVER_EMAIL = os.getenv('SERVER_EMAIL', DEFAULT_FROM_EMAIL) # Email для ошибок сервера 500

# 🔒 Дополнительные настройки безопасности
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY' # Защита от clickjacking
SECURE_REFERRER_POLICY = os.getenv('SECURE_REFERRER_POLICY', 'same-origin') # Контроль заголовка Referer

# 🚫🔍 Защита от индексации поисковыми системами
# Middleware AntiIndexationMiddleware автоматически добавляет:
# - X-Robots-Tag: noindex, nofollow, noarchive, nosnippet
# - Cache-Control для приватных разделов
# - Обрабатывает /robots.txt с Disallow: /admin/, /directory/, /media/

# В production с HTTPS рекомендуется включить:
# SECURE_HSTS_SECONDS = 31536000 # 1 год. Включать только после уверенности в HTTPS
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_SSL_REDIRECT = True # Перенаправлять HTTP на HTTPS на уровне Django (лучше на уровне веб-сервера/балансировщика)

# 🐞 Debug Toolbar настройки
if DEBUG and not TESTING:
    INTERNAL_IPS = ['127.0.0.1', 'localhost'] # IP-адреса, для которых показывать Debug Toolbar
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG and not TESTING, # Условие показа панели
        'SHOW_TEMPLATE_CONTEXT': True, # Показывать контекст шаблонов
        'INTERCEPT_REDIRECTS': False, # Не перехватывать редиректы
        'HIDE_DJANGO_SQL': False, # Не скрывать SQL Django
        'ENABLE_STACKTRACES': True, # Показывать стектрейсы
    }
    DEBUG_TOOLBAR_PANELS = [ # Список панелей
        'debug_toolbar.panels.history.HistoryPanel',
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
        # 'debug_toolbar.panels.profiling.ProfilingPanel', # Можно добавить для профилирования
    ]

# 📝 Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False, # Не отключать существующие логгеры Django
    'formatters': { # Форматы сообщений
        'verbose': {
            'format': '[{levelname}] {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
        'django.server': { # Формат для логов сервера разработки
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },
    'handlers': { # Обработчики логов
        'console': { # Вывод в консоль
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level': 'INFO', # Уровень для консоли (можно DEBUG)
        },
        'file': { # Запись в файл
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs/django.log', # Путь к файлу логов
            'formatter': 'verbose',
            'level': 'DEBUG', # Уровень для файла (более детальный)
            'encoding': 'utf-8', # Явно указываем кодировку UTF-8
        },
        'django.server': { # Обработчик для логов сервера разработки
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        # Можно добавить обработчик для отправки ошибок на email:
        # 'mail_admins': {
        #     'level': 'ERROR',
        #     'class': 'django.utils.log.AdminEmailHandler',
        #     'include_html': True,
        # }
    },
    'root': { # Корневой логгер (ловит все, что не перехвачено другими логгерами)
        'handlers': ['console', 'file'], # Используемые обработчики
        'level': 'INFO', # Общий уровень для корневого логгера
    },
    'loggers': { # Логгеры для конкретных приложений/модулей
        'django': { # Логгер Django
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False, # Не передавать сообщения корневому логгеру, т.к. он их уже обрабатывает
        },
        'django.server': { # Логгер сервера разработки
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.db.backends': { # Логгер для SQL-запросов (если нужно)
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'INFO', # Показывать SQL только в DEBUG
            'propagate': False,
        },
        'directory': { # Логгер для вашего приложения 'directory'
            'handlers': ['file', 'console'],
            'level': 'DEBUG', # Уровень для вашего приложения
            'propagate': True, # Передавать сообщения корневому логгеру
        },
        'exam_security': { # Логгер для безопасности exam поддомена
            'handlers': ['file', 'console'],
            'level': 'WARNING', # Логируем только предупреждения и ошибки
            'propagate': False,
        },
        'pymorphy3.opencorpora_dict.wrapper': { # Логгер для pymorphy3
            'handlers': ['file'],
            'level': 'WARNING', # Скрываем INFO сообщения о загрузке словарей
            'propagate': False,
        },
    },
}

# 💾 Кэширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', # Кэш в памяти (простой, для разработки)
        'LOCATION': 'unique-snowflake', # Уникальное имя для кэша
        # Для production лучше использовать Redis или Memcached:
        # 'BACKEND': 'django_redis.cache.RedisCache',
        # 'LOCATION': 'redis://127.0.0.1:6379/1', # URL вашего Redis сервера
        # 'OPTIONS': {
        #     'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        # }
        # --- или ---
        # 'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
        # 'LOCATION': '127.0.0.1:11211',
    }
}

# Конфигурация для wkhtmltopdf (если используется для генерации PDF)
# Убедитесь, что путь правильный для вашей операционной системы
WKHTMLTOPDF_CMD = os.getenv('WKHTMLTOPDF_CMD', 'C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe') # Пример для Windows
# Для Linux может быть: WKHTMLTOPDF_CMD = os.getenv('WKHTMLTOPDF_CMD', '/usr/bin/wkhtmltopdf')
# Для MacOS (если установлен через Homebrew): WKHTMLTOPDF_CMD = os.getenv('WKHTMLTOPDF_CMD', '/usr/local/bin/wkhtmltopdf')

# 📝 Настройки для экзаменационного поддомена
EXAM_SUBDOMAIN = os.getenv('EXAM_SUBDOMAIN', 'exam.localhost:8001')
EXAM_PROTOCOL = os.getenv('EXAM_PROTOCOL', 'http')