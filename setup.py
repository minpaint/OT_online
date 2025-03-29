# Создайте файл add_column.py в корне проекта
from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("""
    ALTER TABLE directory_position 
    ADD COLUMN can_sign_orders BOOLEAN DEFAULT 0 NOT NULL;
    """)

print("Колонка успешно добавлена")