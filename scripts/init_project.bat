@echo off
python manage.py makemigrations
python manage.py migrate
echo from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').exists() else None | python manage.py shell
python manage.py collectstatic --noinput

echo Project initialized successfully!