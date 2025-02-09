# 📁 create_error_templates.py

import os

# 🎯 Базовый шаблон для страниц ошибок
BASE_ERROR_TEMPLATE = """<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ error_code }} - {{ error_message }}</title>
    <style>
        /* 🎨 Основные стили */
        :root {
            --primary-color: #3498db;
            --error-color: #e74c3c;
            --text-color: #2c3e50;
            --secondary-text: #7f8c8d;
            --bg-color: #f5f5f5;
            --card-bg: white;
            --shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        /* 📱 Общие стили */
        body {
            font-family: 'Segoe UI', Arial, sans-serif;
            background-color: var(--bg-color);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            padding: 1rem;
        }

        /* 🎴 Контейнер ошибки */
        .error-container {
            background-color: var(--card-bg);
            padding: 2.5rem;
            border-radius: 12px;
            box-shadow: var(--shadow);
            text-align: center;
            max-width: 500px;
            width: 100%;
        }

        /* 🔢 Код ошибки */
        .error-code {
            font-size: 5rem;
            color: var(--error-color);
            margin: 0;
            font-weight: bold;
            line-height: 1;
        }

        /* 📝 Сообщение об ошибке */
        .error-message {
            font-size: 1.5rem;
            color: var(--text-color);
            margin: 1rem 0;
        }

        /* ℹ️ Детали ошибки */
        .error-details {
            color: var(--secondary-text);
            margin: 1rem 0;
            font-size: 1rem;
            line-height: 1.5;
        }

        /* 🔄 Кнопка возврата */
        .back-button {
            display: inline-block;
            padding: 0.8rem 1.5rem;
            background-color: var(--primary-color);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: all 0.3s ease;
            font-weight: 500;
            margin-top: 1rem;
        }

        .back-button:hover {
            background-color: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }

        /* 🖼️ Иконка ошибки */
        .error-icon {
            font-size: 4rem;
            margin-bottom: 1rem;
        }

        /* 📱 Адаптивность */
        @media (max-width: 480px) {
            .error-container {
                padding: 1.5rem;
            }
            .error-code {
                font-size: 3rem;
            }
            .error-message {
                font-size: 1.2rem;
            }
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">
            {% if error_code == '404' %}🔍
            {% elif error_code == '403' %}🔒
            {% elif error_code == '500' %}⚠️
            {% else %}❌{% endif %}
        </div>
        <h1 class="error-code">{{ error_code }}</h1>
        <h2 class="error-message">{{ error_message }}</h2>
        {% if error_details %}
            <p class="error-details">{{ error_details }}</p>
        {% endif %}
        <a href="/" class="back-button">Вернуться на главную</a>
    </div>
</body>
</html>
"""

# 📁 Шаблоны для конкретных ошибок
ERROR_TEMPLATES = {
    '400': '{% extends "errors/base_error.html" %}',
    '403': '{% extends "errors/base_error.html" %}',
    '404': '{% extends "errors/base_error.html" %}',
    '500': '{% extends "errors/base_error.html" %}'
}


def create_error_templates():
    """🏗️ Создание шаблонов страниц ошибок"""

    # 📂 Создаем директории, если они не существуют
    template_dir = os.path.join('templates', 'errors')
    os.makedirs(template_dir, exist_ok=True)

    # 📝 Создаем базовый шаблон
    with open(os.path.join(template_dir, 'base_error.html'), 'w', encoding='utf-8') as f:
        f.write(BASE_ERROR_TEMPLATE)
    print('✅ Создан базовый шаблон: base_error.html')

    # 📝 Создаем шаблоны для конкретных ошибок
    for error_code, template_content in ERROR_TEMPLATES.items():
        filename = f'{error_code}.html'
        with open(os.path.join(template_dir, filename), 'w', encoding='utf-8') as f:
            f.write(template_content)
        print(f'✅ Создан шаблон: {filename}')


if __name__ == '__main__':
    try:
        create_error_templates()
        print('\n🎉 Все шаблоны успешно созданы!')
    except Exception as e:
        print(f'\n❌ Ошибка при создании шаблонов: {str(e)}')