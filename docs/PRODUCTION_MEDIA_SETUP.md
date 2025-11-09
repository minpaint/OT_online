# 🚀 Настройка Media файлов для продакшена

## 📋 Оглавление

- [Введение](#введение)
- [Проблема с DEBUG=False](#проблема-с-debugfalse)
- [Решения для продакшена](#решения-для-продакшена)
- [Вариант 1: Nginx](#вариант-1-nginx)
- [Вариант 2: Apache](#вариант-2-apache)
- [Вариант 3: WhiteNoise](#вариант-3-whitenoise)
- [Вариант 4: CDN (S3, Cloudflare R2)](#вариант-4-cdn)
- [Проверка настроек](#проверка-настроек)

---

## Введение

В режиме разработки (`DEBUG=True`) Django автоматически обслуживает media файлы (изображения, загруженные пользователями). Однако **в продакшене** (`DEBUG=False`) это становится проблемой безопасности и производительности.

### ⚠️ Почему Django не обслуживает media в продакшене?

1. **Безопасность**: Django показывает детальные ошибки в DEBUG режиме
2. **Производительность**: Django не оптимизирован для раздачи статических файлов
3. **Масштабируемость**: Веб-серверы (nginx/apache) намного эффективнее

---

## Проблема с DEBUG=False

### Симптомы:

```
❌ Изображения не загружаются в экзаменах
❌ 404 ошибка при доступе к /media/quiz/questions/01.jpg
❌ В консоли браузера: ERR_CONNECTION_REFUSED или 404
```

### Причина:

В `urls.py` media файлы обслуживаются только если `DEBUG=True`:

```python
# ❌ Неправильно - не работает в продакшене
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

## Решения для продакшена

### Текущее временное решение (только для разработки!)

В файле `urls.py` добавлено:

```python
# ⚠️ ВРЕМЕННОЕ РЕШЕНИЕ - только для локального сервера
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Это работает, но НЕ рекомендуется для продакшена!**

---

## Вариант 1: Nginx (Рекомендуется)

### Преимущества:
- ✅ Самый быстрый и эффективный
- ✅ Отличная производительность
- ✅ Низкое потребление памяти
- ✅ Масштабируемость

### Шаг 1: Установка Nginx

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx

# CentOS/RHEL
sudo yum install nginx
```

### Шаг 2: Настройка Nginx

Создайте файл конфигурации: `/etc/nginx/sites-available/sout.by`

```nginx
server {
    listen 80;
    server_name sout.by www.sout.by;

    # Путь к Django проекту
    root /var/www/OT_online;

    # Логи
    access_log /var/log/nginx/sout_access.log;
    error_log /var/log/nginx/sout_error.log;

    # Максимальный размер загружаемых файлов
    client_max_body_size 100M;

    # MEDIA файлы (изображения вопросов)
    location /media/ {
        alias /var/www/OT_online/media/;
        expires 30d;
        add_header Cache-Control "public, immutable";

        # Защита от direct access
        valid_referers none blocked sout.by *.sout.by;
        if ($invalid_referer) {
            return 403;
        }
    }

    # STATIC файлы (CSS, JS)
    location /static/ {
        alias /var/www/OT_online/staticfiles/;
        expires 365d;
        add_header Cache-Control "public, immutable";
    }

    # Django приложение через Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (если нужно)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Шаг 3: Активация конфигурации

```bash
# Создать символическую ссылку
sudo ln -s /etc/nginx/sites-available/sout.by /etc/nginx/sites-enabled/

# Проверить конфигурацию
sudo nginx -t

# Перезапустить Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx
```

### Шаг 4: Настройка прав доступа

```bash
# Права на директорию media
sudo chown -R www-data:www-data /var/www/OT_online/media
sudo chmod -R 755 /var/www/OT_online/media
```

### Шаг 5: Django настройки

В `settings.py`:

```python
DEBUG = False
ALLOWED_HOSTS = ['sout.by', 'www.sout.by']

# Media настройки
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

В `.env`:

```env
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=sout.by,www.sout.by
```

---

## Вариант 2: Apache

### Преимущества:
- ✅ Широко распространен
- ✅ Много документации
- ✅ Поддержка .htaccess

### Шаг 1: Установка Apache

```bash
# Ubuntu/Debian
sudo apt install apache2 libapache2-mod-wsgi-py3

# CentOS/RHEL
sudo yum install httpd mod_wsgi
```

### Шаг 2: Настройка Apache

Создайте файл: `/etc/apache2/sites-available/sout.by.conf`

```apache
<VirtualHost *:80>
    ServerName sout.by
    ServerAlias www.sout.by
    ServerAdmin admin@sout.by

    # Логи
    ErrorLog ${APACHE_LOG_DIR}/sout_error.log
    CustomLog ${APACHE_LOG_DIR}/sout_access.log combined

    # MEDIA файлы
    Alias /media/ /var/www/OT_online/media/
    <Directory /var/www/OT_online/media>
        Require all granted
        Options -Indexes

        # Кэширование
        ExpiresActive On
        ExpiresDefault "access plus 30 days"
    </Directory>

    # STATIC файлы
    Alias /static/ /var/www/OT_online/staticfiles/
    <Directory /var/www/OT_online/staticfiles>
        Require all granted
        Options -Indexes
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </Directory>

    # WSGI Django
    WSGIDaemonProcess sout python-home=/var/www/OT_online/venv python-path=/var/www/OT_online
    WSGIProcessGroup sout
    WSGIScriptAlias / /var/www/OT_online/wsgi.py

    <Directory /var/www/OT_online>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>
</VirtualHost>
```

### Шаг 3: Активация

```bash
# Включить модули
sudo a2enmod expires
sudo a2enmod headers
sudo a2enmod wsgi

# Активировать сайт
sudo a2ensite sout.by.conf

# Перезапустить Apache
sudo systemctl restart apache2
sudo systemctl enable apache2
```

---

## Вариант 3: WhiteNoise (Простое решение)

### Преимущества:
- ✅ Простая установка
- ✅ Не требует настройки веб-сервера
- ✅ Хорошо для небольших проектов
- ⚠️ Менее производительно чем nginx

### Шаг 1: Установка

```bash
pip install whitenoise
```

### Шаг 2: Настройка в settings.py

```python
# Добавить в MIDDLEWARE (после SecurityMiddleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← Добавить здесь
    # ... остальные middleware
]

# Настройки для static файлов
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# WhiteNoise НЕ обслуживает MEDIA файлы!
# Для media используйте nginx или CDN
```

**⚠️ Важно:** WhiteNoise обслуживает только STATIC файлы, но не MEDIA! Для media все равно нужен nginx или CDN.

---

## Вариант 4: CDN (Amazon S3, Cloudflare R2)

### Преимущества:
- ✅ Глобальное распределение (CDN)
- ✅ Высокая доступность
- ✅ Автоматическое резервное копирование
- ✅ Масштабируемость
- ⚠️ Стоимость хранения

### Amazon S3 + django-storages

#### Шаг 1: Установка

```bash
pip install django-storages boto3
```

#### Шаг 2: Настройка settings.py

```python
# Добавить в INSTALLED_APPS
INSTALLED_APPS = [
    # ...
    'storages',
]

# AWS настройки
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = 'eu-central-1'  # Ваш регион
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'

# Media файлы в S3
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
```

#### Шаг 3: Настройка .env

```env
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=sout-media
```

#### Шаг 4: Создание S3 bucket

```bash
# AWS CLI
aws s3 mb s3://sout-media --region eu-central-1

# Настройка публичного доступа
aws s3api put-bucket-policy --bucket sout-media --policy file://bucket-policy.json
```

`bucket-policy.json`:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::sout-media/media/*"
        }
    ]
}
```

### Cloudflare R2 (дешевле S3)

#### Преимущества R2:
- ✅ Нет платы за исходящий трафик
- ✅ Совместим с S3 API
- ✅ Дешевле чем S3

#### Настройка:

```python
# settings.py
AWS_S3_ENDPOINT_URL = 'https://<account-id>.r2.cloudflarestorage.com'
AWS_S3_REGION_NAME = 'auto'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## Проверка настроек

### 1. Проверка доступности media файлов

```bash
# Прямой доступ через curl
curl -I http://sout.by/media/quiz/questions/01.jpg

# Должен вернуть:
# HTTP/1.1 200 OK
# Content-Type: image/jpeg
```

### 2. Проверка прав доступа

```bash
# Проверить владельца
ls -la /var/www/OT_online/media/quiz/questions/

# Должно быть:
# -rw-r--r-- www-data www-data
```

### 3. Проверка Django

```python
# manage.py shell
from django.conf import settings
from directory.models import Question

q = Question.objects.filter(image__isnull=False).first()
print(f"Image URL: {q.image.url}")
print(f"Expected: /media/quiz/questions/{q.image.name}")
```

### 4. Проверка логов Nginx

```bash
# Логи доступа
sudo tail -f /var/log/nginx/sout_access.log

# Логи ошибок
sudo tail -f /var/log/nginx/sout_error.log
```

---

## 🔒 Безопасность

### Защита от hotlinking (прямых ссылок)

```nginx
location /media/ {
    alias /var/www/OT_online/media/;

    # Разрешить доступ только с вашего домена
    valid_referers none blocked sout.by *.sout.by;
    if ($invalid_referer) {
        return 403;
    }
}
```

### Ограничение размера загрузки

```nginx
# Nginx
client_max_body_size 100M;
```

```python
# Django settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100MB
```

---

## 📊 Мониторинг

### Проверка использования диска

```bash
# Размер media директории
du -sh /var/www/OT_online/media

# Топ-10 самых больших файлов
find /var/www/OT_online/media -type f -exec du -h {} + | sort -rh | head -10
```

### Очистка старых файлов (опционально)

```bash
# Удалить файлы старше 90 дней
find /var/www/OT_online/media/tmp -type f -mtime +90 -delete
```

---

## ❓ FAQ

### Q: Нужно ли перезапускать Django после настройки nginx?

A: Нет, nginx обслуживает media файлы напрямую, минуя Django.

### Q: Можно ли использовать и nginx, и S3 одновременно?

A: Да! Новые файлы грузите в S3, а nginx будет кэшировать их локально.

### Q: Как мигрировать существующие media файлы в S3?

A: Используйте AWS CLI:
```bash
aws s3 sync ./media/ s3://sout-media/media/
```

### Q: WhiteNoise достаточно для небольшого проекта?

A: Только для STATIC файлов. Для MEDIA все равно нужен nginx или S3.

---

## 🎯 Рекомендации

### Для небольшого проекта (< 1000 пользователей):
1. **Nginx** для media/static - простая и быстрая настройка

### Для среднего проекта (1000-10000 пользователей):
1. **Nginx** + кэширование
2. **CDN** для static файлов (Cloudflare)

### Для крупного проекта (> 10000 пользователей):
1. **Nginx** или **Apache** как reverse proxy
2. **S3/R2** для хранения media
3. **CloudFront/Cloudflare CDN** для раздачи
4. **Redis** для кэширования

---

## 📚 Дополнительные ресурсы

- [Django Deployment Checklist](https://docs.djangoproject.com/en/stable/howto/deployment/checklist/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Django-storages Documentation](https://django-storages.readthedocs.io/)
- [WhiteNoise Documentation](http://whitenoise.evans.io/)

---

## ✅ Чеклист для продакшена

- [ ] `DEBUG=False` в `.env`
- [ ] Настроен nginx/apache для media файлов
- [ ] Проверен доступ к `/media/quiz/questions/01.jpg`
- [ ] Настроены права доступа (`www-data:www-data`)
- [ ] Включено кэширование media файлов
- [ ] Настроена защита от hotlinking
- [ ] Настроено ограничение размера загрузки
- [ ] Настроен мониторинг использования диска
- [ ] Настроено резервное копирование media директории
- [ ] Протестированы изображения в экзаменах

---

**Дата создания:** 03.11.2025
**Версия:** 1.0
**Автор:** Claude Code Assistant
