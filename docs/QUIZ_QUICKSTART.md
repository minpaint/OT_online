# Быстрый старт - Система тестирования по ОТ

## Что реализовано

✅ **Backend полностью готов:**
1. Модели данных (6 моделей)
2. Админ-панель с nested_admin
3. Views для прохождения квизов
4. URL-маршруты
5. Миграции базы данных применены

## Быстрый запуск

### 1. Создание категории и вопросов через админку

```bash
# Запустить сервер
python manage.py runserver

# Перейти в админку
http://127.0.0.1:8000/admin/
```

**Шаги в админке:**

1. **Создать категорию** (`QuizCategory`):
   - Название: "Общие вопросы по охране труда"
   - Порядок: 1
   - Активна: ✓

2. **Создать вопросы** (`Question`):
   - Выбрать категорию
   - Текст вопроса: "Что обязан предпринять работодатель..."
   - Добавить изображение (опционально)
   - Добавить 4 варианта ответа через inline-форму
   - Отметить правильный ответ галочкой "Правильный ответ"

3. **Создать квиз** (`Quiz`):
   - Название: "Тестирование по ОТ"
   - Тип: "Обучение по теме" или "Экзамен"
   - Категория: выбрать созданную
   - Проходной балл: 80
   - Показывать правильный ответ сразу: ✓
   - Разрешить пропускать вопросы: ✓
   - Активен: ✓

### 2. Прохождение квиза

Перейти на:
```
http://127.0.0.1:8000/quiz/
```

## Структура URL

| URL | Описание |
|-----|----------|
| `/quiz/` | Список квизов |
| `/quiz/<quiz_id>/start/` | Начать квиз |
| `/quiz/<attempt_id>/question/<n>/` | Вопрос №N |
| `/quiz/<attempt_id>/result/` | Результаты |
| `/quiz/history/` | История прохождений |

## Что нужно сделать дальше

### Обязательно (для работы):
- [ ] Создать HTML-шаблоны с дизайном из изображений
- [ ] Написать CSS стили
- [ ] Добавить JavaScript для AJAX-отправки ответов

### Опционально (улучшения):
- [ ] Management command для парсинга вопросов из изображений
- [ ] Расширенная статистика
- [ ] Экспорт/импорт вопросов через Excel
- [ ] Таймер для экзаменов
- [ ] Генерация сертификатов

## Создание тестовых данных программно

```python
python manage.py shell

from directory.models import QuizCategory, Quiz, Question, Answer

# Создать категорию
category = QuizCategory.objects.create(
    name="Общие вопросы по охране труда",
    description="Базовые знания",
    order=1,
    is_active=True
)

# Создать вопрос
question = Question.objects.create(
    category=category,
    question_text="Что обязан предпринять работодатель?",
    is_active=True
)

# Добавить ответы
Answer.objects.create(
    question=question,
    answer_text="Назначить лиц ответственных",
    is_correct=True,
    order=1
)

Answer.objects.create(
    question=question,
    answer_text="Организовать систематическое наблюдение",
    is_correct=False,
    order=2
)

# ... еще 2 ответа

# Создать квиз
quiz = Quiz.objects.create(
    title="Обучение по ОТ",
    quiz_type='training',
    category=category,
    random_order=True,
    show_correct_answer=True,
    allow_skip=True,
    is_active=True
)

print(f"Создан квиз: {quiz.title}")
print(f"Вопросов в категории: {category.get_questions_count()}")
```

## Проверка работы

```bash
# Проверить модели
python manage.py check

# Показать миграции
python manage.py showmigrations directory

# Проверить админку
python manage.py runserver
# Открыть http://127.0.0.1:8000/admin/directory/
```

## Структура файлов

```
directory/
├── models/quiz.py           ✅ Создано
├── admin/quiz_admin.py      ✅ Создано
├── views/quiz_views.py      ✅ Создано
├── urls.py                  ✅ Обновлено
├── templates/directory/quiz/
│   ├── quiz_list.html       ⏳ Нужно создать
│   ├── quiz_question.html   ⏳ Нужно создать
│   └── quiz_result.html     ⏳ Нужно создать
└── static/directory/
    ├── css/quiz.css         ⏳ Нужно создать
    └── js/quiz.js           ⏳ Нужно создать
```

## Примеры использования

### Получить все квизы:
```python
from directory.models import Quiz
quizzes = Quiz.objects.filter(is_active=True)
```

### Начать прохождение:
```python
from directory.models import Quiz, QuizAttempt
from django.contrib.auth.models import User

quiz = Quiz.objects.get(id=1)
user = User.objects.get(username='admin')

attempt = QuizAttempt.objects.create(
    quiz=quiz,
    user=user,
    total_questions=quiz.get_total_questions()
)
```

### Подсчитать результат:
```python
attempt.calculate_score()
print(f"Результат: {attempt.score_percentage}%")
print(f"Пройден: {attempt.passed}")
```

## Следующие шаги

1. Создать базовые HTML-шаблоны для тестирования
2. Добавить несколько тестовых вопросов через админку
3. Проверить прохождение квиза
4. Разработать финальный дизайн на основе изображений
5. Добавить JavaScript для интерактивности

## Полная документация

См. `QUIZ_SYSTEM.md` для детальной информации.
