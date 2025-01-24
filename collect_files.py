import os


def read_and_print_files():
    # Корневая директория проекта
    project_root = "D:/YandexDisk/OT_online"

    # Структура файлов для анализа
    files_to_analyze = {
        'Models': [
            'core/models/base.py',
            'core/models/department.py',
            'core/models/division.py',
            'core/models/document.py',
            'core/models/employee.py',
            'core/models/hierarchy.py',
            'core/models/organization.py',
            'core/models/position.py',
            'core/models/__init__.py'
        ],
        'Forms': [
            'core/forms.py'
        ],
        'Views': [
            'core/views.py',
            'core/api/views.py'
        ],
        'URLs': [
            'core/urls.py',
            'core/api/urls.py'
        ],
        'Services': [
            'core/services/document_service.py',
            'core/services/employee_service.py',
            'core/services/organization_service.py'
        ],
        'Signals': [
            'core/signals/__init__.py'
        ],
        'Static JS': [
            'core/static/js/dependent_dropdowns.js',
            'core/static/admin/js/dependent_dropdowns.js'
        ],
        'Templates': [
            'core/templates/core/organization_form.html',
            'core/templates/core/position_form.html'
        ]
    }

    for category, files in files_to_analyze.items():
        print(f"\n{'=' * 80}\n{category}\n{'=' * 80}")

        for file_path in files:
            full_path = os.path.join(project_root, file_path)

            try:
                if os.path.exists(full_path):
                    print(f"\n--- {file_path} ---\n")
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        print(content)
                else:
                    print(f"\nFile not found: {file_path}")
            except Exception as e:
                print(f"\nError reading {file_path}: {str(e)}")


if __name__ == "__main__":
    read_and_print_files()