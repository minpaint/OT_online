# 📧 Email уведомления о медицинских осмотрах

## Описание

Management команда `send_medical_notifications` отправляет email уведомления о плане прохождения медицинских осмотров.

## Использование

### Базовая команда

```bash
python manage.py send_medical_notifications
```

Отправит уведомление всем администраторам (пользователи с `is_staff=True` и заполненным email).

### Параметры

**--emails** - указать конкретные email адреса (через запятую):
```bash
python manage.py send_medical_notifications --emails="admin@example.com,hr@example.com"
```

**--organization** - фильтровать по организации:
```bash
python manage.py send_medical_notifications --organization=1
```

### Комбинированное использование

```bash
python manage.py send_medical_notifications --emails="ot@company.ru" --organization=2
```

## Содержание письма

Email содержит три секции:

1. **📋 Требуется внести дату медосмотра** - сотрудники без указанной даты первичного медосмотра
2. **🚨 Просроченные медосмотры** - сотрудники с истекшим сроком медосмотра
3. **⚠️ Предстоящие медосмотры** - сотрудники, которым нужно пройти медосмотр в ближайшие 30 дней

## Настройка автоматической отправки (Cron)

### Linux/Mac

Добавьте в crontab:

```bash
# Открыть crontab
crontab -e

# Отправка 1 и 15 числа каждого месяца в 9:00
0 9 1,15 * * cd /path/to/project && /path/to/venv/bin/python manage.py send_medical_notifications

# Или через settings_prod.py
0 9 1,15 * * cd /path/to/project && /path/to/venv/bin/python manage.py send_medical_notifications --settings=settings_prod
```

### Windows (Task Scheduler)

1. Откройте **Планировщик заданий** (Task Scheduler)
2. Создайте новое задание
3. **Триггер**: 1 и 15 число каждого месяца в 9:00
4. **Действие**: Запустить программу
   - Программа: `C:\venvs\OT_online\Scripts\python.exe`
   - Аргументы: `manage.py send_medical_notifications`
   - Рабочая папка: `G:\Мой диск\OT_online`

## Настройка Email в Django

Убедитесь, что в `settings.py` настроена отправка email:

```python
# Email настройки
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'  # или ваш SMTP сервер
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'OT Online <noreply@company.com>'
```

### Для тестирования (консольный вывод)

```python
# В settings.py для разработки
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

## Тестирование

Проверьте команду вручную:

```bash
# Тестовая отправка себе
python manage.py send_medical_notifications --emails="your@email.com"

# Проверка без отправки (console backend)
python manage.py send_medical_notifications
```

## Устранение проблем

### Ошибка: "No module named 'deadline_control.management'"

Убедитесь, что созданы все `__init__.py` файлы:
- `deadline_control/management/__init__.py`
- `deadline_control/management/commands/__init__.py`

### Ошибка: "SMTPAuthenticationError"

Проверьте:
1. Правильность email и пароля
2. Включена ли двухфакторная аутентификация (используйте App Password для Gmail)
3. Доступ для менее безопасных приложений (если используется Gmail)

### Нет получателей

Убедитесь, что у администраторов заполнено поле email:
```python
# В Django shell
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(is_staff=True).values_list('email', flat=True)
```

## Примеры использования

### Еженедельная отправка всем администраторам

```bash
# Каждый понедельник в 9:00
0 9 * * 1 cd /path/to/project && /path/to/venv/bin/python manage.py send_medical_notifications
```

### Отправка конкретному отделу

```bash
# 1 и 15 числа в 10:00 для конкретной организации
0 10 1,15 * * cd /path/to/project && /path/to/venv/bin/python manage.py send_medical_notifications --emails="hr@company.ru" --organization=1
```
