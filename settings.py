import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.contrib.messages import constants as messages

# 📌 Загрузка переменных окружения из файла .env
load_dotenv()

# 📂 Определяем корневой каталог проекта
BASE_DIR = Path(__file__).resolve().parent

# 🧪 Определяем, запущены ли тесты
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

# 🔐 Основные настройки безопасности
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True' and not TESTING
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# 📱 Базовые приложения
DJANGO_APPS = [
    'django.contrib.admin',      # Админка Django 👨‍💼
    'django.contrib.auth',         # Аутентификация 🔑
    'django.contrib.contenttypes', # Типы контента 📄
    'django.contrib.sessions',     # Сессии пользователя 🕑
    'django.contrib.messages',     # Сообщения 📨
    'django.contrib.staticfiles',  # Статические файлы 🖼️
]

# 🔌 Сторонние приложения
THIRD_PARTY_APPS = [
    'corsheaders',              # CORS настройки 🌐
    'django_extensions',        # Расширения Django ⚙️
    'mptt',                     # Для древовидных структур 📊
    'dal',                      # Django Autocomplete Light 🔍
    'dal_select2',              # Виджеты Select2 для DAL 🎯
    'crispy_forms',             # Красивые формы ✨
    'crispy_bootstrap4',        # Bootstrap 4 для crispy-forms 🎨
]

# 🏠 Локальные приложения
LOCAL_APPS = [
    'directory.apps.DirectoryConfig',  # Наше приложение "directory" 📦
]

# Добавляем debug_toolbar только если не в режиме тестирования
if not TESTING and DEBUG:
    THIRD_PARTY_APPS.append('debug_toolbar')

# Объединяем все приложения
INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# 🛠️ Базовый middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',     # Защита 🔒
    'django.contrib.sessions.middleware.SessionMiddleware',# Сессии 🕑
    'corsheaders.middleware.CorsMiddleware',               # CORS 🌐
    'django.middleware.common.CommonMiddleware',           # Общие настройки 🔧
    'django.middleware.csrf.CsrfViewMiddleware',           # CSRF защита 🚫
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Аутентификация 🔑
    'django.contrib.messages.middleware.MessageMiddleware',     # Сообщения 📨
    'django.middleware.clickjacking.XFrameOptionsMiddleware',   # Защита от clickjacking 🖱️
]

# Добавляем debug_toolbar middleware только если не в режиме тестирования
if not TESTING and DEBUG:
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# 🌐 URL-конфигурация
ROOT_URLCONF = 'urls'

# 📄 Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Рекомендуется хранить глобальные шаблоны в BASE_DIR / 'templates'
        'DIRS': [
            BASE_DIR / 'templates',
            # Если в каталоге directory/templates есть уникальные шаблоны, оставьте, иначе можно удалить
            BASE_DIR / 'directory' / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media',
            ],
        },
    },
]

# 🌍 WSGI-приложение
WSGI_APPLICATION = 'wsgi.application'

# 💾 База данных (по умолчанию SQLite)
if os.getenv('DATABASE_URL', '').startswith('sqlite'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
            'TEST': {
                'NAME': BASE_DIR / 'test_db.sqlite3',
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
USE_TZ = True

# 📁 Статические файлы
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
    BASE_DIR / 'directory' / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# 📸 Медиа файлы
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# 🔑 Тип первичного ключа
DEFAULT_AUTO_FIELD = os.getenv('DEFAULT_AUTO_FIELD', 'django.db.models.BigAutoField')

# 🔗 CORS настройки
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# 🔐 Настройки аутентификации
LOGIN_URL = 'directory:auth:login'
LOGIN_REDIRECT_URL = 'directory:home'
LOGOUT_REDIRECT_URL = 'directory:auth:login'
AUTH_USER_MODEL = 'auth.User'

# 🍪 Настройки сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 3600  # 1 час
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SECURE = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# 🔒 CSRF настройки
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# 🎨 Настройки форм (crispy-forms)
CRISPY_TEMPLATE_PACK = 'bootstrap4'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap4'
CRISPY_FAIL_SILENTLY = not DEBUG

# 💬 Настройки сообщений
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
MESSAGE_TAGS = {
    messages.DEBUG: 'alert-secondary',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# 🌐 Настройки для Select2 (если вы решите использовать локальные файлы, но сейчас через CDN)
SELECT2_JS = 'vendor/select2/dist/js/select2.min.js'
SELECT2_CSS = 'vendor/select2/dist/css/select2.min.css'
SELECT2_I18N_PATH = 'vendor/select2/dist/js/i18n'

# 🔍 Настройки для django-autocomplete-light
DAL_MAX_RESULTS = 10
DAL_FORWARD_FIELDS = True
DAL_DELETE_ON_AJAX = True

# 🎯 Настройки для MPTT
MPTT_ADMIN_LEVEL_INDENT = 20
MPTT_DEFAULT_LEVEL_INDICATOR = '---'

# 📧 Email настройки
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# 🔒 Дополнительные настройки безопасности
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'

# 🐞 Debug Toolbar настройки
if DEBUG and not TESTING:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
        'SHOW_TEMPLATE_CONTEXT': True,
        'INTERCEPT_REDIRECTS': False,
        'IS_RUNNING_TESTS': False,
    }
    DEBUG_TOOLBAR_PANELS = [
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
    ]

# 📝 Логирование
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django.log',
            'level': 'DEBUG',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'directory': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# 💾 Кэширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
