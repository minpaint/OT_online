from django.contrib.auth.models import User
from directory.models import Profile

for user in User.objects.all():
    print(f"Обрабатываю пользователя: {user.username}") # Добавлено для отслеживания
    if not hasattr(user, 'profile'):
        try:
            Profile.objects.create(user=user)
            print(f"  Профиль создан для пользователя: {user.username}")
        except Exception as e:
            print(f"  Ошибка создания профиля для пользователя: {user.username} - {e}")
    else:
        print(f"  Профиль уже существует для пользователя: {user.username}")

print("Процесс создания профилей завершен.")