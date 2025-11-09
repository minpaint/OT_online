# TODO: Система квизов/экзаменов

## Текущее состояние (29.10.2025)

### Что уже работает ✅
- Модели: QuizCategory, Quiz, Question, Answer, QuizAttempt, UserAnswer
- Views: quiz_list, quiz_start, quiz_question, quiz_answer, quiz_result, quiz_history
- Админка полностью настроена с nested_admin
- Миграции 0025-0028 применены
- В БД: 1 категория, 2 квиза, 121 вопрос
- URL-маршруты настроены

### Найденные проблемы ❌
1. **Отсутствует шаблон `templates/directory/quiz/category_detail.html`** (вызывает 500 ошибку)
   - View `category_detail` существует в quiz_views.py:449
   - URL настроен: `path('category/<int:category_id>/', ...)`
   - Но шаблона нет!

2. Нет глобальных настроек для экзаменов (по скриншоту Screenshot_1.jpg)

---

## План реализации глобальных настроек

### Концепция
- **Singleton модель QuizSettings** - единственный экземпляр на всю систему
- Применяется ко всем квизам глобально
- Система оценки: только "Сдал/Не сдал" (без процентов)

### Этап 1: Создать модель QuizSettings

**Файл:** `directory/models/quiz_settings.py`

**Поля модели:**

#### Блок "Общие параметры отображения"
- `show_theme_name` - BooleanField - показывать название темы
- `show_error_count` - BooleanField - показывать количество ошибок
- `show_preliminary_score` - BooleanField - показывать предварительную оценку
- `show_correct_answers` - BooleanField - показывать правильные/неправильные ответы
- `show_comments` - CharField(choices) - когда показывать комментарии:
  - `after_any` - после любого ответа
  - `after_wrong` - после неправильного ответа
  - `never` - никогда
- `show_exit_button` - BooleanField - показывать кнопку "Выход"
- `show_skip_button` - BooleanField - показывать кнопку "Пропустить"
- `early_completion_mode` - CharField(choices) - досрочное завершение при лимите ошибок:
  - `none` - нет
  - `suggest` - предлагать завершить (диалог)
  - `auto` - завершать сразу

#### Блок "Настройки таймера"
- `timer_mode` - CharField(choices):
  - `disabled` - отключен
  - `per_question` - на каждый ответ
  - `total_answers` - на общее время всех ответов
  - `total_exam` - на общее время экзамена
- `timer_per_question_seconds` - IntegerField(default=60) - время на вопрос
- `timer_total_exam_minutes` - IntegerField(default=30) - общее время экзамена
- `timeout_action` - CharField(choices) - действие при истечении:
  - `warning` - предупреждение
  - `finish_exam` - завершить экзамен
  - `mark_incorrect` - считать ответ неправильным

#### Блок "Оформление"
- `fail_screen_red` - BooleanField - красный фон при провале

**Методы:**
```python
@classmethod
def get_settings(cls):
    """Singleton: получить единственный экземпляр"""
    settings, created = cls.objects.get_or_create(pk=1)
    return settings

def save(self, *args, **kwargs):
    """Всегда сохранять с pk=1 (singleton)"""
    self.pk = 1
    super().save(*args, **kwargs)

def delete(self, *args, **kwargs):
    """Запретить удаление"""
    pass
```

### Этап 2: Миграция

**Файл:** `directory/migrations/0029_add_quiz_settings.py`

Создать таблицу QuizSettings с дефолтными значениями.

### Этап 3: Админка

**Файл:** `directory/admin/quiz_admin.py`

Добавить:
```python
@admin.register(QuizSettings)
class QuizSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False  # Singleton - нельзя создавать новые

    def has_delete_permission(self, request, obj=None):
        return False  # Нельзя удалять

    fieldsets = (
        ('Общие параметры отображения', {...}),
        ('Настройки таймера', {...}),
        ('Оформление', {...}),
    )
```

### Этап 4: Обновить Views

**Файл:** `directory/views/quiz_views.py`

В каждом view добавить:
```python
settings = QuizSettings.get_settings()
context['settings'] = settings
```

**Изменить логику:**

1. **quiz_question** (показ вопроса):
   - Учитывать `settings.show_theme_name`
   - Учитывать `settings.show_error_count`
   - Учитывать `settings.show_preliminary_score`
   - Передавать настройки таймера в контекст
   - Добавить кнопку выхода если `show_exit_button`
   - Добавить кнопку пропуска если `show_skip_button`

2. **quiz_answer** (обработка ответа):
   - Учитывать `settings.show_comments` - когда показывать explanation
   - Реализовать `early_completion_mode`:
     - `suggest` - вернуть флаг для показа диалога
     - `auto` - сразу завершать попытку
   - Обрабатывать `timeout_action` при истечении времени

3. **quiz_result** (результаты):
   - Применять `fail_screen_red` для непрошедших тестов

### Этап 5: Обновить шаблоны

**Файл:** `templates/directory/quiz/quiz_question.html`

Добавить условия:
```html
{% if settings.show_theme_name %}
    <h2>{{ question.category.name }}</h2>
{% endif %}

{% if settings.show_error_count %}
    <div class="error-counter">
        Ошибок: {{ attempt.incorrect_answers }}
        {% if attempt.allowed_incorrect_answers > 0 %}
            / {{ attempt.allowed_incorrect_answers }}
        {% endif %}
    </div>
{% endif %}

{% if settings.show_preliminary_score %}
    <div class="score-preview">
        Правильных ответов: {{ attempt.correct_answers }} / {{ answered_count }}
    </div>
{% endif %}

{% if settings.show_exit_button %}
    <button class="btn btn-danger" onclick="confirmExit()">Выход</button>
{% endif %}
```

**Файл:** `templates/directory/quiz/quiz_result.html`

```html
<div class="result-container {% if settings.fail_screen_red and not attempt.passed %}bg-danger{% endif %}">
    ...
</div>
```

### Этап 6: JavaScript для таймеров

**Файл:** `static/js/quiz_timer.js` (создать новый)

Реализовать:
1. Таймер на каждый вопрос (`timer_per_question_seconds`)
2. Таймер на весь экзамен (`timer_total_exam_minutes`)
3. Действия при истечении времени:
   - `warning` - показать предупреждение
   - `finish_exam` - редирект на результаты
   - `mark_incorrect` - автоматически отправить пустой ответ

### Этап 7: Обновить модель Quiz

**НЕ НУЖНО** - все настройки глобальные в QuizSettings.

Но можно оставить в Quiz:
- `exam_time_limit` - как дефолт если timer_mode != disabled
- `exam_allowed_incorrect` - лимит ошибок для досрочного завершения
- `allow_skip` - будет перезаписан глобальной настройкой

---

## Приоритизация (ждет уточнения от пользователя)

### Вопросы:
1. Что важнее сначала:
   - [ ] Исправить ошибку 500 (создать category_detail.html)
   - [ ] Реализовать глобальные настройки

2. Какие настройки критичны сейчас:
   - [ ] Таймеры
   - [ ] Отображение ошибок
   - [ ] Кнопки выхода/пропуска
   - [ ] Все сразу

3. Оставить ли `score_percentage` для статистики или убрать совсем?

4. "Предлагать завершить" - показывать modal диалог?

---

## Порядок реализации (после уточнения)

### Фаза 1: Критические исправления
- [ ] Создать `templates/directory/quiz/category_detail.html`
- [ ] Протестировать что /directory/quiz/ работает

### Фаза 2: Глобальные настройки (базовая версия)
- [ ] Создать модель QuizSettings
- [ ] Создать миграцию 0029
- [ ] Добавить в admin
- [ ] Обновить __init__.py для импорта модели

### Фаза 3: Интеграция в views
- [ ] Обновить quiz_question
- [ ] Обновить quiz_answer
- [ ] Обновить quiz_result

### Фаза 4: Обновление шаблонов
- [ ] quiz_question.html - добавить условия отображения
- [ ] quiz_result.html - красный фон при провале

### Фаза 5: JavaScript
- [ ] Создать quiz_timer.js
- [ ] Интегрировать в quiz_question.html
- [ ] Реализовать все режимы таймера

### Фаза 6: Тестирование
- [ ] Протестировать все режимы таймера
- [ ] Протестировать досрочное завершение
- [ ] Протестировать отображение ошибок
- [ ] Протестировать кнопки выхода/пропуска

---

## Технические детали

### Структура файлов
```
directory/
├── models/
│   ├── __init__.py         # добавить импорт QuizSettings
│   ├── quiz.py             # существующие модели
│   └── quiz_settings.py    # НОВЫЙ ФАЙЛ
├── views/
│   └── quiz_views.py       # обновить все views
├── admin/
│   └── quiz_admin.py       # добавить QuizSettingsAdmin
└── migrations/
    └── 0029_add_quiz_settings.py  # НОВАЯ МИГРАЦИЯ

templates/directory/quiz/
├── quiz_list.html          # существующий
├── quiz_question.html      # ОБНОВИТЬ
├── quiz_result.html        # ОБНОВИТЬ
├── quiz_history.html       # существующий
└── category_detail.html    # СОЗДАТЬ!

static/js/
└── quiz_timer.js           # СОЗДАТЬ
```

### Зависимости
- Нет новых зависимостей
- Используем стандартный Django
- JavaScript - vanilla JS или можно jQuery

---

## Заметки

- Система только "Сдал/Не сдал" - проценты для статистики
- Singleton pattern для QuizSettings - только 1 запись в БД
- Глобальные настройки перезаписывают индивидуальные настройки Quiz
- Таймеры работают через JavaScript + AJAX проверка на сервере
