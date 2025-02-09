import os
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Определяем корневой каталог проекта (например, D:\YandexDisk\OT_online)
BASE_DIR = Path(__file__).resolve().parent
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_wsgi_application()
