"""
📝 Resource для импорта/экспорта вопросов викторин
"""
from import_export import resources, fields, widgets
from directory.models import Question, Answer, QuizCategory
from django.core.exceptions import ValidationError


class QuizQuestionResource(resources.ModelResource):
    """
    📝 Ресурс для экспорта вопросов викторины с ответами.

    Экспортирует вопросы в формате:
    - Номер вопроса (order)
    - Раздел
    - Текст вопроса
    - Ответ 1, 2, 3, 4... (с указанием правильного)
    - Пояснение
    - Путь к изображению
    """

    # Основные поля
    order = fields.Field(
        column_name='Номер вопроса',
        attribute='order'
    )

    category_name = fields.Field(
        column_name='Раздел',
        attribute='category',
        widget=widgets.CharWidget()
    )

    question_text = fields.Field(
        column_name='Текст вопроса',
        attribute='question_text',
        widget=widgets.CharWidget()
    )

    # Поля для ответов (до 10 вариантов)
    answer_1 = fields.Field(column_name='Ответ 1', readonly=True)
    answer_2 = fields.Field(column_name='Ответ 2', readonly=True)
    answer_3 = fields.Field(column_name='Ответ 3', readonly=True)
    answer_4 = fields.Field(column_name='Ответ 4', readonly=True)
    answer_5 = fields.Field(column_name='Ответ 5', readonly=True)
    answer_6 = fields.Field(column_name='Ответ 6', readonly=True)
    answer_7 = fields.Field(column_name='Ответ 7', readonly=True)
    answer_8 = fields.Field(column_name='Ответ 8', readonly=True)
    answer_9 = fields.Field(column_name='Ответ 9', readonly=True)
    answer_10 = fields.Field(column_name='Ответ 10', readonly=True)

    correct_answer_number = fields.Field(
        column_name='Номер правильного ответа',
        readonly=True
    )

    explanation = fields.Field(
        column_name='Пояснение',
        attribute='explanation',
        widget=widgets.CharWidget()
    )

    image_path = fields.Field(
        column_name='Путь к изображению',
        readonly=True
    )

    has_image = fields.Field(
        column_name='Есть изображение',
        readonly=True
    )

    is_active = fields.Field(
        column_name='Активен',
        attribute='is_active',
        widget=widgets.BooleanWidget()
    )

    class Meta:
        model = Question
        fields = (
            'order',
            'category_name',
            'question_text',
            'answer_1', 'answer_2', 'answer_3', 'answer_4', 'answer_5',
            'answer_6', 'answer_7', 'answer_8', 'answer_9', 'answer_10',
            'correct_answer_number',
            'explanation',
            'image_path',
            'has_image',
            'is_active',
        )
        export_order = fields
        skip_unchanged = False

    def dehydrate_category_name(self, question):
        """Экспортируем название раздела"""
        return question.category.name if question.category else ''

    def dehydrate_answer_1(self, question):
        """Экспортируем текст первого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[0].answer_text if len(answers) > 0 else ''

    def dehydrate_answer_2(self, question):
        """Экспортируем текст второго ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[1].answer_text if len(answers) > 1 else ''

    def dehydrate_answer_3(self, question):
        """Экспортируем текст третьего ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[2].answer_text if len(answers) > 2 else ''

    def dehydrate_answer_4(self, question):
        """Экспортируем текст четвертого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[3].answer_text if len(answers) > 3 else ''

    def dehydrate_answer_5(self, question):
        """Экспортируем текст пятого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[4].answer_text if len(answers) > 4 else ''

    def dehydrate_answer_6(self, question):
        """Экспортируем текст шестого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[5].answer_text if len(answers) > 5 else ''

    def dehydrate_answer_7(self, question):
        """Экспортируем текст седьмого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[6].answer_text if len(answers) > 6 else ''

    def dehydrate_answer_8(self, question):
        """Экспортируем текст восьмого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[7].answer_text if len(answers) > 7 else ''

    def dehydrate_answer_9(self, question):
        """Экспортируем текст девятого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[8].answer_text if len(answers) > 8 else ''

    def dehydrate_answer_10(self, question):
        """Экспортируем текст десятого ответа"""
        answers = list(question.answers.order_by('order'))
        return answers[9].answer_text if len(answers) > 9 else ''

    def dehydrate_correct_answer_number(self, question):
        """Экспортируем номер правильного ответа (1-based)"""
        answers = list(question.answers.order_by('order'))
        for idx, answer in enumerate(answers, 1):
            if answer.is_correct:
                return idx
        return ''

    def dehydrate_image_path(self, question):
        """Экспортируем путь к изображению"""
        if question.image:
            return question.image.name
        return ''

    def dehydrate_has_image(self, question):
        """Экспортируем флаг наличия изображения"""
        return 'Да' if question.image else 'Нет'

    def get_export_queryset(self, queryset=None):
        """Оптимизация для экспорта"""
        qs = super().get_export_queryset(queryset)
        return qs.select_related('category').prefetch_related('answers')
