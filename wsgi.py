import os
import sys
from pathlib import Path
from django.core.wsgi import get_wsgi_application

# Добавляем текущую директорию в PYTHONPATH
current_path = Path(__file__).resolve().parent
sys.path.append(str(current_path))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings')

application = get_wsgi_application()