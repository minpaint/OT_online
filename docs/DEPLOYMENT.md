# 🚀 Руководство по развёртыванию OT_online

Полная инструкция по развёртыванию системы управления охраной труда на домашнем сервере с автоматическим деплоем через GitHub Actions.

## 📋 Содержание

- [Архитектура деплоя](#архитектура-деплоя)
- [Требования к серверу](#требования-к-серверу)
- [Первоначальная настройка сервера](#первоначальная-настройка-сервера)
- [Настройка GitHub Actions](#настройка-github-actions)
- [Ручной деплой](#ручной-деплой)
- [Обновления и миграции](#обновления-и-миграции)
- [Мониторинг и логи](#мониторинг-и-логи)
- [Резервное копирование](#резервное-копирование)
- [Решение проблем](#решение-проблем)

---

## 🏗️ Архитектура деплоя

```
Локальная разработка (Windows)
        ↓
    git push
        ↓
    GitHub Repository
        ↓
  GitHub Actions (CI/CD)
        ↓
    SSH Deploy
        ↓
Домашний сервер (Linux)
    ├── Nginx (веб-сервер)
    ├── Gunicorn (WSGI)
    ├── Django (приложение)
    └── PostgreSQL (база данных)
```

---

## 💻 Требования к серверу

### Минимальные требования:
- **ОС**: Ubuntu 20.04+ / Debian 11+
- **RAM**: 2 GB (рекомендуется 4 GB)
- **CPU**: 2 ядра
- **Диск**: 20 GB свободного места
- **Python**: 3.10+
- **PostgreSQL**: 14+
- **Nginx**: 1.18+

### Необходимое ПО:
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib nginx git
```

---

## 🔧 Первоначальная настройка сервера

### 1. Создание пользователя для приложения

```bash
# Создаём системного пользователя
sudo useradd -m -s /bin/bash ot_user

# Добавляем в группу www-data для работы с Nginx
sudo usermod -aG www-data ot_user
```

### 2. Настройка PostgreSQL

```bash
# Переключаемся на пользователя postgres
sudo -u postgres psql

-- В psql создаём базу данных и пользователя
CREATE DATABASE ot_online;
CREATE USER ot_user WITH PASSWORD 'your_secure_password';
ALTER ROLE ot_user SET client_encoding TO 'utf8';
ALTER ROLE ot_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ot_user SET timezone TO 'Europe/Moscow';
GRANT ALL PRIVILEGES ON DATABASE ot_online TO ot_user;
\q
```

### 3. Клонирование репозитория

```bash
# Создаём директорию для проекта
sudo mkdir -p /var/www/ot_online
sudo chown -R ot_user:www-data /var/www/ot_online
sudo chmod 755 /var/www/ot_online

# Переключаемся на пользователя проекта
sudo su - ot_user

# Клонируем репозиторий
cd /var/www/ot_online
git clone https://github.com/minpaint/OT_online.git .
```

### 4. Создание виртуального окружения

```bash
# Создаём виртуальное окружение
python3 -m venv venv

# Активируем
source venv/bin/activate

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Настройка переменных окружения

```bash
# Копируем пример .env
cp .env.example .env

# Редактируем .env
nano .env
```

**Важные переменные в `.env`:**

```bash
# Django
DJANGO_SECRET_KEY=your-generated-secret-key-here
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DJANGO_SETTINGS_MODULE=settings_prod

# База данных
DATABASE_URL=postgresql://ot_user:your_secure_password@localhost:5432/ot_online

# Exam subdomain
EXAM_SUBDOMAIN=exam.yourdomain.com
EXAM_PROTOCOL=https

# Безопасность
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://exam.yourdomain.com
```

**Генерация SECRET_KEY:**
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### 6. Первоначальная миграция и сборка статики

```bash
# Применяем миграции
python manage.py migrate

# Собираем статику
python manage.py collectstatic --noinput

# Создаём суперпользователя
python manage.py createsuperuser
```

### 7. Настройка Gunicorn как системной службы

Создаём файл службы:
```bash
sudo nano /etc/systemd/system/ot_online.service
```

Содержимое файла:
```ini
[Unit]
Description=OT_online Gunicorn daemon
After=network.target postgresql.service

[Service]
Type=notify
User=ot_user
Group=www-data
RuntimeDirectory=gunicorn
WorkingDirectory=/var/www/ot_online
Environment="PATH=/var/www/ot_online/venv/bin"
Environment="DJANGO_SETTINGS_MODULE=settings_prod"
EnvironmentFile=/var/www/ot_online/.env
ExecStart=/var/www/ot_online/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/gunicorn/ot_online.sock \
    --timeout 60 \
    --log-level info \
    --access-logfile /var/log/ot_online/access.log \
    --error-logfile /var/log/ot_online/error.log \
    wsgi:application
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Создаём директорию для логов:
```bash
sudo mkdir -p /var/log/ot_online
sudo chown -R ot_user:www-data /var/log/ot_online
```

Запускаем службу:
```bash
sudo systemctl daemon-reload
sudo systemctl start ot_online
sudo systemctl enable ot_online
sudo systemctl status ot_online
```

### 8. Настройка Nginx

Создаём конфигурацию:
```bash
sudo nano /etc/nginx/sites-available/ot_online
```

Содержимое файла:
```nginx
# Основной домен
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Редирект на HTTPS (после получения SSL)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/ot_online/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/ot_online/media/;
        expires 7d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/ot_online.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }
}

# Exam поддомен
server {
    listen 80;
    server_name exam.yourdomain.com;

    # Редирект на HTTPS (после получения SSL)
    # return 301 https://$server_name$request_uri;

    client_max_body_size 50M;

    location /static/ {
        alias /var/www/ot_online/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /var/www/ot_online/media/;
        expires 7d;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/run/gunicorn/ot_online.sock;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Host $http_host;
        proxy_redirect off;
    }

    # Дополнительная защита для exam поддомена
    add_header X-Robots-Tag "noindex, nofollow, noarchive" always;
}
```

Активируем конфигурацию:
```bash
sudo ln -s /etc/nginx/sites-available/ot_online /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Получение SSL сертификата (Let's Encrypt)

```bash
# Устанавливаем certbot
sudo apt install certbot python3-certbot-nginx

# Получаем сертификаты для обоих доменов
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com -d exam.yourdomain.com

# Проверяем автообновление
sudo certbot renew --dry-run
```

---

## 🔐 Настройка GitHub Actions

### 1. Генерация SSH ключа для деплоя

На сервере:
```bash
# Генерируем SSH ключ (без пароля)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/github_deploy

# Добавляем публичный ключ в authorized_keys
cat ~/.ssh/github_deploy.pub >> ~/.ssh/authorized_keys

# Выводим приватный ключ для копирования
cat ~/.ssh/github_deploy
```

### 2. Добавление секретов в GitHub

Перейдите в **Settings → Secrets and variables → Actions** вашего репозитория и добавьте:

| Имя секрета | Значение | Описание |
|-------------|----------|----------|
| `SSH_PRIVATE_KEY` | Содержимое `~/.ssh/github_deploy` | Приватный SSH ключ |
| `SERVER_HOST` | `192.168.1.100` или `yourdomain.com` | IP или домен сервера |
| `SERVER_USER` | `ot_user` | Пользователь для SSH |
| `PROJECT_DIR` | `/var/www/ot_online` | Директория проекта |

### 3. Разрешение sudo без пароля для рестарта службы

На сервере:
```bash
sudo visudo
```

Добавьте в конец файла:
```
ot_user ALL=(ALL) NOPASSWD: /bin/systemctl restart ot_online
ot_user ALL=(ALL) NOPASSWD: /bin/systemctl reload nginx
ot_user ALL=(ALL) NOPASSWD: /usr/sbin/nginx -t
```

### 4. Тестирование автодеплоя

После настройки просто сделайте push в main:
```bash
git add .
git commit -m "Test auto-deploy"
git push origin main
```

Проверьте выполнение в **Actions** на GitHub.

---

## 🛠️ Ручной деплой

Если нужно задеплоить вручную, используйте скрипт `deploy.sh`:

```bash
# На сервере
cd /var/www/ot_online
bash deploy.sh
```

Или по шагам:
```bash
# 1. Обновление кода
git pull origin main

# 2. Активация venv
source venv/bin/activate

# 3. Обновление зависимостей
pip install -r requirements.txt

# 4. Миграции
python manage.py migrate

# 5. Сборка статики
python manage.py collectstatic --noinput

# 6. Перезапуск
sudo systemctl restart ot_online
sudo systemctl reload nginx
```

---

## 🔄 Обновления и миграции

### Создание миграций

На локальной машине:
```bash
py manage.py makemigrations --name describe_migration
py manage.py migrate
git add directory/migrations/
git commit -m "Add migration: describe_migration"
git push
```

### Откат миграций

На сервере (в случае проблем):
```bash
cd /var/www/ot_online
source venv/bin/activate
python manage.py migrate directory 0035  # Откат к версии 0035
sudo systemctl restart ot_online
```

---

## 📊 Мониторинг и логи

### Просмотр логов приложения

```bash
# Логи Gunicorn
sudo journalctl -u ot_online -f

# Логи Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Логи приложения
sudo tail -f /var/log/ot_online/access.log
sudo tail -f /var/log/ot_online/error.log
```

### Проверка статуса служб

```bash
# Статус Django приложения
sudo systemctl status ot_online

# Статус Nginx
sudo systemctl status nginx

# Статус PostgreSQL
sudo systemctl status postgresql
```

### Мониторинг ресурсов

```bash
# Использование памяти и CPU
htop

# Размер базы данных
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('ot_online'));"

# Место на диске
df -h
```

---

## 💾 Резервное копирование

### Автоматический бэкап базы данных

Создайте скрипт `/home/ot_user/backup_db.sh`:
```bash
#!/bin/bash
DATE=$(date +"%Y%m%d_%H%M%S")
BACKUP_DIR="/var/backups/ot_online"
mkdir -p $BACKUP_DIR

# Бэкап базы данных
pg_dump -U ot_user ot_online | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Удаление старых бэкапов (старше 7 дней)
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_$DATE.sql.gz"
```

Добавьте в cron (каждый день в 3:00):
```bash
crontab -e
```
```
0 3 * * * /home/ot_user/backup_db.sh >> /var/log/ot_online_backup.log 2>&1
```

### Восстановление из бэкапа

```bash
# Остановка приложения
sudo systemctl stop ot_online

# Восстановление БД
gunzip < /var/backups/ot_online/db_20250101_030000.sql.gz | sudo -u postgres psql ot_online

# Запуск приложения
sudo systemctl start ot_online
```

---

## 🔍 Решение проблем

### Ошибка: "502 Bad Gateway"

**Причина**: Gunicorn не запущен или сокет недоступен.

**Решение**:
```bash
sudo systemctl status ot_online
sudo journalctl -u ot_online -n 50
sudo systemctl restart ot_online
```

### Ошибка: "Database connection failed"

**Причина**: PostgreSQL недоступен или неверные учётные данные.

**Решение**:
```bash
sudo systemctl status postgresql
sudo -u postgres psql -l  # Проверка доступных БД
# Проверьте .env файл
```

### Ошибка: "Static files not found (404)"

**Причина**: Статика не собрана или неверный путь в Nginx.

**Решение**:
```bash
cd /var/www/ot_online
source venv/bin/activate
python manage.py collectstatic --noinput
sudo nginx -t && sudo systemctl reload nginx
```

### GitHub Actions не может подключиться по SSH

**Причина**: Неверный SSH ключ или firewall блокирует подключение.

**Решение**:
```bash
# Проверьте SSH ключ на сервере
cat ~/.ssh/authorized_keys | grep github-actions

# Проверьте firewall
sudo ufw status
sudo ufw allow 22/tcp  # Если порт SSH заблокирован
```

---

## 📞 Поддержка

Если возникли проблемы:

1. Проверьте логи (см. раздел "Мониторинг и логи")
2. Проверьте статус всех служб
3. Создайте Issue в GitHub репозитории с описанием проблемы и логами

---

## 📝 Чеклист деплоя

- [ ] Сервер настроен (PostgreSQL, Nginx, Python)
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] `.env` файл настроен
- [ ] Миграции применены
- [ ] Суперпользователь создан
- [ ] Gunicorn служба запущена
- [ ] Nginx настроен
- [ ] SSL сертификат получен
- [ ] GitHub Secrets добавлены
- [ ] Автодеплой протестирован
- [ ] Бэкапы настроены

---

**Удачного деплоя! 🚀**
