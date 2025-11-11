#!/bin/bash
# OT_online Production Deployment Script
# Автоматический деплой на домашний сервер

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Конфигурация
PROJECT_DIR="/var/www/ot_online"
VENV_DIR="$PROJECT_DIR/venv"
REPO_URL="https://github.com/minpaint/OT_online.git"
BRANCH="main"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   OT_online Deployment Started${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. Проверка наличия директории проекта
if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}Директория проекта не найдена. Создаём...${NC}"
    sudo mkdir -p "$PROJECT_DIR"
    sudo chown -R $USER:$USER "$PROJECT_DIR"
    cd "$PROJECT_DIR"
    git clone "$REPO_URL" .
else
    cd "$PROJECT_DIR"
fi

# 2. Обновление кода из GitHub
echo -e "${GREEN}[1/8] Обновление кода из GitHub...${NC}"
git fetch origin
git reset --hard origin/$BRANCH

# 3. Проверка виртуального окружения
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${GREEN}[2/8] Создание виртуального окружения...${NC}"
    python3 -m venv "$VENV_DIR"
fi

# 4. Активация виртуального окружения
echo -e "${GREEN}[3/8] Активация виртуального окружения...${NC}"
source "$VENV_DIR/bin/activate"

# 5. Обновление зависимостей
echo -e "${GREEN}[4/8] Установка/обновление зависимостей...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 6. Миграции базы данных
echo -e "${GREEN}[5/8] Применение миграций...${NC}"
python manage.py migrate --noinput

# 7. Сборка статики
echo -e "${GREEN}[6/8] Сборка статических файлов...${NC}"
python manage.py collectstatic --noinput

# 8. Перезапуск службы
echo -e "${GREEN}[7/8] Перезапуск службы...${NC}"
if systemctl is-active --quiet ot_online; then
    sudo systemctl restart ot_online
    echo -e "${GREEN}Служба ot_online перезапущена${NC}"
else
    echo -e "${YELLOW}Служба ot_online не найдена. Запуск gunicorn вручную...${NC}"
    # Закрываем старый процесс gunicorn, если есть
    pkill -f "gunicorn.*ot_online" || true
    # Запускаем gunicorn в фоне
    gunicorn --daemon \
        --workers 3 \
        --bind unix:/var/www/ot_online/ot_online.sock \
        --env DJANGO_SETTINGS_MODULE=settings_prod \
        wsgi:application
fi

# 9. Перезапуск Nginx
echo -e "${GREEN}[8/8] Перезапуск Nginx...${NC}"
if command -v nginx &> /dev/null; then
    sudo nginx -t && sudo systemctl reload nginx
else
    echo -e "${YELLOW}Nginx не найден. Пропускаем...${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Completed Successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Проверьте статус службы: ${YELLOW}sudo systemctl status ot_online${NC}"
echo -e "Просмотр логов: ${YELLOW}sudo journalctl -u ot_online -f${NC}"
