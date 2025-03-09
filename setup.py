# update_siz_card.py
import os
import re

# Путь к файлу шаблона
template_file_path = 'directory/templates/directory/siz_issued/personal_card.html'

# Проверяем существование файла
if not os.path.exists(template_file_path):
    print(f"Ошибка: файл {template_file_path} не найден!")
    exit(1)

# Читаем содержимое файла
with open(template_file_path, 'r', encoding='utf-8') as file:
    content = file.read()

# Определяем содержимое для замены вкладки "Нормы выдачи" (Лицевая сторона)
norms_tab_content = '''
<!-- Вкладка "Нормы выдачи" (Лицевая сторона) -->
<div class="tab-pane fade show active" id="norms" role="tabpanel" aria-labelledby="norms-tab">
    <div class="card">
        <div class="siz-card-header">
            ЛИЧНАЯ КАРТОЧКА № {{ employee.id }}
            учета средств индивидуальной защиты
        </div>
        <div class="card-body">
            <!-- Сведения о работнике -->
            <div class="employee-info-section">
                <h4 class="section-header">Сведения о работнике</h4>

                <div class="row employee-info-row">
                    <div class="col-md-8 col-sm-7">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Фамилия, собственное имя, отчество (если таковое имеется):</div>
                            <div class="col-md-8 employee-info-value">{{ employee.full_name_nominative }}</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-2">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Пол</div>
                            <div class="col-md-8 employee-info-value">Мужской</div>
                        </div>
                    </div>
                    <div class="col-md-2 col-sm-3">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Рост</div>
                            <div class="col-md-8 employee-info-value">{{ employee.height|default:"" }}</div>
                        </div>
                    </div>
                </div>

                <div class="row employee-info-row">
                    <div class="col-md-8 col-sm-7">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Структурное подразделение</div>
                            <div class="col-md-8 employee-info-value">
                                {% if employee.department %}
                                    {{ employee.department.name }}
                                {% elif employee.subdivision %}
                                    {{ employee.subdivision.name }}
                                {% else %}
                                    Непродовольственный отдел
                                {% endif %}
                            </div>
                        </div>
                    </div>
                    <div class="col-md-4 col-sm-5">
                        <div class="row">
                            <div class="col-md-6 col-sm-6">
                                <div class="row">
                                    <div class="col-md-6 employee-info-label">Размер:</div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 employee-info-label">одежды</div>
                                    <div class="col-md-6 employee-info-value">{{ employee.clothing_size|default:"" }}</div>
                                </div>
                            </div>
                            <div class="col-md-6 col-sm-6">
                                <div class="row">
                                    <div class="col-md-6 employee-info-label">обуви</div>
                                    <div class="col-md-6 employee-info-value">{{ employee.shoe_size|default:"" }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="row employee-info-row">
                    <div class="col-md-8 col-sm-7">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Профессия (должность):</div>
                            <div class="col-md-8 employee-info-value">{{ employee.position.position_name }}</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-sm-5">
                        <div class="row">
                            <div class="col-md-6 employee-info-label">СИЗ головы</div>
                            <div class="col-md-6 employee-info-value">56</div>
                        </div>
                    </div>
                </div>

                <div class="row employee-info-row">
                    <div class="col-md-8 col-sm-7">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Дата поступления на работу</div>
                            <div class="col-md-8 employee-info-value">{{ employee.date_of_birth|date:"d.m.Y" }}</div>
                        </div>
                    </div>
                    <div class="col-md-4 col-sm-5">
                        <div class="row">
                            <div class="col-md-6 employee-info-label">СИЗОД</div>
                            <div class="col-md-6 employee-info-value">3</div>
                        </div>
                    </div>
                </div>

                <div class="row employee-info-row">
                    <div class="col-md-8 col-sm-7">
                        <div class="row">
                            <div class="col-md-4 employee-info-label">Дата изменения профессии (должности)</div>
                            <div class="col-md-8 employee-info-value"></div>
                        </div>
                    </div>
                    <div class="col-md-4 col-sm-5">
                        <div class="row">
                            <div class="col-md-6 employee-info-label">СИЗ рук</div>
                            <div class="col-md-6 employee-info-value">9</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Предусмотрено по установленным нормам -->
            <div class="norms-section">
                <h4 class="section-header mt-3 mb-3">Предусмотрено по установленным нормам</h4>

                <table class="table table-bordered siz-table">
                    <thead>
                        <tr>
                            <th class="siz-name">Наименование средств индивидуальной защиты</th>
                            <th class="siz-classification">Классификация (маркировка) средства индивидуальной защиты по защитным свойствам</th>
                            <th class="siz-unit">Единица измерения</th>
                            <th class="siz-quantity">Количество</th>
                            <th class="siz-period">Срок носки в месяцах</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for norm in base_norms %}
                        <tr>
                            <td class="siz-name">{{ norm.siz.name }}</td>
                            <td class="siz-classification">{{ norm.siz.classification }}</td>
                            <td class="siz-unit">{{ norm.siz.unit }}</td>
                            <td class="siz-quantity">{{ norm.quantity }}</td>
                            <td class="siz-period">
                                {% if norm.siz.wear_period == 0 %}
                                    До износа
                                {% else %}
                                    {{ norm.siz.wear_period }}
                                {% endif %}
                            </td>
                        </tr>
                        {% endfor %}

                        {% for group in condition_groups %}
                        <tr class="condition-row">
                            <td colspan="5">{{ group.name }}:</td>
                        </tr>
                            {% for norm in group.norms %}
                            <tr>
                                <td class="siz-name">{{ norm.siz.name }}</td>
                                <td class="siz-classification">{{ norm.siz.classification }}</td>
                                <td class="siz-unit">{{ norm.siz.unit }}</td>
                                <td class="siz-quantity">{{ norm.quantity }}</td>
                                <td class="siz-period">
                                    {% if norm.siz.wear_period == 0 %}
                                        До износа
                                    {% else %}
                                        {{ norm.siz.wear_period }}
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Подписи -->
            <div class="signatures-section">
                <div class="row signature-row">
                    <div class="col-md-6">
                        <div class="signature-label">Главный бухгалтер (бухгалтер)</div>
                        <div class="signature-line"></div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-12">
                        <div class="signature-label">Согласовано:</div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-6">
                        <div class="signature-label">специалист отдела кадров</div>
                        <div class="signature-line"></div>
                        <div class="signature-comment">(личная подпись, инициалы, разборчивая подпись)</div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-6">
                        <div class="signature-label">руководитель структурного подразделения</div>
                        <div class="signature-line"></div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-6">
                        <div class="signature-label">специалист по охране труда</div>
                        <div class="signature-line"></div>
                        <div class="signature-comment">(личная подпись, инициалы, разборчивая подпись)</div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-6">
                        <div class="signature-label">ответственное лицо за выдачу СИЗ</div>
                        <div class="signature-line"></div>
                        <div class="signature-comment">(личная подпись, инициалы, разборчивая подпись)</div>
                    </div>
                </div>

                <div class="row signature-row">
                    <div class="col-md-12">
                        <div class="signature-label">Ознакомлен работник:</div>
                        <div class="signature-line"></div>
                        <div class="signature-comment">(личная подпись, инициалы, разборчивая подпись)</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
'''

# Определяем содержимое для замены/добавления стилей
additional_styles = '''
/* Стили для личной карточки учета СИЗ по форме МБ-7 */
.siz-card-header {
    background-color: #007bff;
    color: white;
    padding: 0.75rem 1.5rem;
    font-weight: bold;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    text-align: center;
    font-size: 1.2rem;
}

.employee-info-section {
    padding: 10px;
    border-bottom: 1px solid #dee2e6;
}

.section-header {
    text-align: center;
    font-weight: bold;
    margin-bottom: 10px;
}

.employee-info-row {
    margin-bottom: 8px;
}

.employee-info-label {
    font-weight: bold;
}

.employee-info-value {
    border: 1px solid #999;
    padding: 3px 8px;
    min-height: 24px;
    background-color: #f9f9f9;
}

.siz-table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
}

.siz-table th, 
.siz-table td {
    border: 1px solid #000;
    padding: 5px;
    text-align: center;
    vertical-align: middle;
}

.siz-table th {
    background-color: #f0f0f0;
    font-weight: bold;
}

.siz-table .siz-name {
    text-align: left;
    width: 35%;
}

.siz-table .siz-classification {
    width: 20%;
}

.siz-table .siz-unit {
    width: 10%;
}

.siz-table .siz-quantity {
    width: 15%;
}

.siz-table .siz-period {
    width: 20%;
}

.condition-row {
    background-color: #e6f2ff;
    font-style: italic;
}

.signatures-section {
    padding: 10px;
    margin-top: 20px;
}

.signature-row {
    margin-bottom: 15px;
}

.signature-label {
    font-weight: bold;
}

.signature-line {
    border-bottom: 1px solid #000;
    min-width: 200px;
    display: inline-block;
    margin: 0 10px;
}

.signature-comment {
    font-size: 0.8rem;
    color: #666;
    margin-top: 5px;
}

/* Дополнительные стили для печати */
@media print {
    .employee-info-value {
        background-color: transparent !important;
    }

    .siz-card-header {
        background-color: transparent !important;
        color: black !important;
        border: 1px solid #000 !important;
        text-transform: uppercase;
    }

    .siz-table th {
        background-color: transparent !important;
    }

    .condition-row {
        background-color: transparent !important;
    }
}
'''


# Функция для замены вкладки "Нормы выдачи" (Лицевая сторона)
def replace_norms_tab(content):
    """
    🔄 Заменяет содержимое вкладки "Нормы выдачи"
    """
    # Шаблон для поиска вкладки
    pattern = r'<!-- Вкладка "Нормы выдачи" \(Лицевая сторона\) -->\s*<div class="tab-pane fade show active"[^>]*>.*?</div>\s*<!-- Вкладка "Выданные СИЗ"'

    # Замена с сохранением закрывающего тега вкладки
    replacement = norms_tab_content + '\n<!-- Вкладка "Выданные СИЗ"'

    # Выполняем замену с учетом многострочного режима
    result = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return result


# Функция для добавления стилей
def add_styles(content):
    """
    🎨 Добавляет стили в блок extra_css
    """
    # Шаблон для поиска блока стилей
    pattern = r'{% block extra_css %}\s*<style>.*?</style>\s*{% endblock %}'

    # Новое содержимое блока стилей
    replacement = f'{{% block extra_css %}}\n<style>\n{additional_styles}\n/* Существующие стили */\n/* 🎨 Стили для личной карточки учета СИЗ */\n.card-header {{\n    background-color: #f5f5f5;\n    padding: 1rem;\n}}\n\n.card-body {{\n    padding: 1.5rem;\n}}\n\n.siz-group {{\n    margin-bottom: 1.5rem;\n    border: 1px solid #dee2e6;\n    border-radius: 4px;\n}}\n\n.siz-group-header {{\n    padding: 0.75rem 1rem;\n    background-color: #f8f9fa;\n    border-bottom: 1px solid #dee2e6;\n    font-weight: bold;\n}}\n\n.siz-table-container {{\n    overflow-x: auto;\n}}\n\n.nav-link.active {{\n    background-color: #007bff !important;\n    color: white !important;\n}}\n\n.badge-active {{\n    background-color: #28a745;\n    color: white;\n}}\n\n.badge-returned {{\n    background-color: #dc3545;\n    color: white;\n}}\n\n.print-btn {{\n    margin-bottom: 1rem;\n}}\n\n/* 🖨️ Стили для печати */\n@media print {{\n    .no-print {{\n        display: none !important;\n    }}\n\n    .container {{\n        width: 100%;\n        max-width: 100%;\n    }}\n\n    .card {{\n        border: none !important;\n    }}\n\n    .card-header {{\n        border-bottom: 1px solid #000 !important;\n    }}\n\n    .table {{\n        border-collapse: collapse !important;\n    }}\n\n    .table td,\n    .table th {{\n        border: 1px solid #000 !important;\n    }}\n}}\n</style>\n{{% endblock %}}'

    # Выполняем замену с учетом многострочного режима
    result = re.sub(pattern, replacement, content, flags=re.DOTALL)
    return result


# Модификация представления для объединения эталонных и прямых норм
def modify_view():
    """
    🔄 Модифицирует представление для получения норм СИЗ с учетом эталонных норм
    """
    view_file_path = 'directory/views/siz_issued.py'

    # Проверяем существование файла
    if not os.path.exists(view_file_path):
        print(f"Ошибка: файл {view_file_path} не найден!")
        return False

    # Читаем содержимое файла
    with open(view_file_path, 'r', encoding='utf-8') as file:
        view_content = file.read()

    # Шаблон для поиска метода get_context_data в классе SIZPersonalCardView
    pattern = r'def get_context_data\(self, \*\*kwargs\):\s*"""[\s\S]*?"""[\s\S]*?context\[\'condition_groups\'\] = condition_groups'

    # Новое содержимое метода
    replacement = '''def get_context_data(self, **kwargs):
        """
        📊 Добавляем дополнительные данные в контекст
        """
        context = super().get_context_data(**kwargs)
        context['title'] = f'Личная карточка учета СИЗ - {self.object.full_name_nominative}'

        # Получаем все выданные сотруднику СИЗ
        issued_items = SIZIssued.objects.filter(
            employee=self.object
        ).select_related('siz').order_by('-issue_date')

        context['issued_items'] = issued_items

        # Получаем нормы СИЗ для должности сотрудника
        if self.object.position:
            # 🆕 Улучшенная логика получения норм: объединяем конкретные и эталонные
            position = self.object.position

            # 1. Получаем непосредственные нормы должности
            direct_norms = SIZNorm.objects.filter(
                position=position
            ).select_related('siz')

            # 2. Получаем эталонные нормы по названию должности
            reference_norms = Position.find_reference_norms(position.position_name)

            # 3. Формируем словарь норм, где ключ - комбинация siz_id + condition
            norm_dict = {}

            # Сначала добавляем эталонные нормы (они будут перезаписаны прямыми при совпадении)
            for norm in reference_norms:
                key = f"{norm.siz_id}_{norm.condition}"
                norm_dict[key] = norm

            # Затем добавляем прямые нормы с более высоким приоритетом
            for norm in direct_norms:
                key = f"{norm.siz_id}_{norm.condition}"
                norm_dict[key] = norm

            # 4. Группируем нормы по условиям
            base_norms = []
            condition_groups = {}

            for key, norm in norm_dict.items():
                if not norm.condition:
                    base_norms.append(norm)
                else:
                    if norm.condition not in condition_groups:
                        condition_groups[norm.condition] = []
                    condition_groups[norm.condition].append(norm)

            # 5. Сортируем нормы по порядку (order) и названию СИЗ
            base_norms.sort(key=lambda x: (x.order, x.siz.name))

            context['base_norms'] = base_norms
            context['condition_groups'] = [
                {'name': condition, 'norms': sorted(norms, key=lambda x: (x.order, x.siz.name))}
                for condition, norms in condition_groups.items()
            ]'''

    # Выполняем замену с учетом многострочного режима
    modified_view_content = re.sub(pattern, replacement, view_content, flags=re.DOTALL)

    # Записываем обновленный файл
    with open(view_file_path, 'w', encoding='utf-8') as file:
        file.write(modified_view_content)

    return True


# Выполняем модификации шаблона
content = replace_norms_tab(content)
content = add_styles(content)

# Записываем обновленный файл
with open(template_file_path, 'w', encoding='utf-8') as file:
    file.write(content)

# Модифицируем представление
modify_view_success = modify_view()

print(f"✅ Шаблон {template_file_path} успешно обновлен!")
if modify_view_success:
    print(f"✅ Представление успешно обновлено!")
else:
    print(f"❌ Не удалось обновить представление.")