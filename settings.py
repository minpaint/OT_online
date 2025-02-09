import os
from pathlib import Path
from dotenv import load_dotenv

# 📌 Загрузка переменных окружения из файла .env
load_dotenv()

# 📂 Определяем корневой каталог проекта (D:\YandexDisk\OT_online)
BASE_DIR = Path(__file__).resolve().parent

# 🔐 Основные настройки безопасности
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# 📱 Установленные приложения (apps)
INSTALLED_APPS = [
    'django.contrib.admin',         # Админка Django 👨‍💼
    'django.contrib.auth',          # Аутентификация 🔑
    'django.contrib.contenttypes',  # Типы контента 📄
    'django.contrib.sessions',      # Сессии пользователя 🕑
    'django.contrib.messages',      # Сообщения 📨
    'django.contrib.staticfiles',   # Статические файлы 🖼️

    'corsheaders',                  # CORS настройки 🌐
    'debug_toolbar',                # Debug Toolbar 🐞
    'django_extensions',            # Расширения Django ⚙️
    'directory.apps.DirectoryConfig',  # Наше приложение "directory" 📦
    'mptt',                         # Для древовидных структур 📊
    'dal',                          # Django Autocomplete Light для автодополнения 🔍
    'dal_select2',                  # Виджеты Select2 для DAL 🎯
]

# 🛠️ Middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # Отображение отладочной панели 🐞
    'django.middleware.security.SecurityMiddleware',      # Защита (security) 🔒
    'django.contrib.sessions.middleware.SessionMiddleware',  # Работа с сессиями 🕑
    'corsheaders.middleware.CorsMiddleware',              # CORS обработка 🌐
    'django.middleware.common.CommonMiddleware',          # Общие настройки 🔧
    'django.middleware.csrf.CsrfViewMiddleware',          # Защита от CSRF атак 🚫
    'django.contrib.auth.middleware.AuthenticationMiddleware',  # Аутентификация пользователей 🔑
    'django.contrib.messages.middleware.MessageMiddleware',  # Передача сообщений 📨
    'django.middleware.clickjacking.XFrameOptionsMiddleware',  # Защита от clickjacking 🖱️
]

# 🌐 Основной URL-конфигурация
ROOT_URLCONF = 'urls'

# 📄 Настройки шаблонов
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Папка с шаблонами в корне проекта 📂
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',   # Отладка 🐞
                'django.template.context_processors.request',   # Объект запроса
                'django.contrib.auth.context_processors.auth',  # Аутентификация
                'django.contrib.messages.context_processors.messages',  # Сообщения
            ],
        },
    },
]

# 🌍 WSGI-приложение
WSGI_APPLICATION = 'wsgi.application'

# 💾 Настройки базы данных (SQLite)
if os.getenv('DATABASE_URL', '').startswith('sqlite'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',  # Файл базы создаётся в корне проекта
        }
    }

# 🔒 Валидаторы паролей
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# 🌍 Интернационализация
LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ru-ru')
TIME_ZONE = os.getenv('TIME_ZONE', 'Europe/Moscow')
USE_I18N = True
USE_TZ = True

# 📁 Статические файлы
STATIC_URL = os.getenv('STATIC_URL', '/static/')
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# 📸 Медиа файлы
MEDIA_URL = os.getenv('MEDIA_URL', '/media/')
MEDIA_ROOT = BASE_DIR / 'media'

# 🔑 Тип первичного ключа по умолчанию
DEFAULT_AUTO_FIELD = os.getenv('DEFAULT_AUTO_FIELD', 'django.db.models.BigAutoField')

# 🔗 Настройки CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# Настройки сессий
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 86400
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_SECURE = False

# 🔒 Настройки CSRF
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_COOKIE_SECURE = False
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# 📧 Настройки Email
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

if DEBUG:
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'SHOW_TEMPLATE_CONTEXT': True,
        'INTERCEPT_REDIRECTS': False,
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

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler',},
        'file': {'class': 'logging.FileHandler', 'filename': BASE_DIR / 'django.log', 'level': 'DEBUG',},
    },
    'root': {'handlers': ['console', 'file'], 'level': 'INFO',},
    'loggers': {
        'directory': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CACHES = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',}
}
