# directory/views/quiz_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db.models import Q
from typing import Optional
import random
from directory.models import (
    Quiz, QuizCategory, Question, Answer, QuizAttempt, UserAnswer, QuizAccessToken, QuizQuestionOrder
)


def _get_time_left_seconds(attempt: QuizAttempt) -> Optional[int]:
    """Возвращает оставшееся время в секундах или None, если лимита нет."""
    if attempt.time_limit_seconds <= 0:
        return None
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    return max(0, int(attempt.time_limit_seconds - elapsed))


def _find_first_skipped_question(attempt: QuizAttempt) -> Optional[int]:
    """Найти номер первого пропущенного вопроса (1-indexed) или None, если все отвечены."""
    # Получаем все вопросы попытки в правильном порядке
    question_orders = QuizQuestionOrder.objects.filter(attempt=attempt).order_by('order')

    for qo in question_orders:
        # Проверяем, есть ли ответ на этот вопрос
        user_answer = UserAnswer.objects.filter(
            attempt=attempt,
            question_id=qo.question_id,
            is_skipped=True
        ).first()

        if user_answer:
            # Нашли пропущенный вопрос, возвращаем его номер (order + 1)
            return qo.order + 1

    return None


def _finalize_attempt(attempt: QuizAttempt, request, failure_reason: str = QuizAttempt.FAILURE_NONE):
    """Фиксируем завершение попытки и очищаем сессию."""
    if attempt.status != QuizAttempt.STATUS_COMPLETED:
        if attempt.failure_reason != failure_reason:
            attempt.failure_reason = failure_reason
        attempt.status = QuizAttempt.STATUS_COMPLETED
        attempt.completed_at = timezone.now()
        attempt.save(update_fields=['failure_reason', 'status', 'completed_at'])
        attempt.calculate_score()

    session_key = f'quiz_questions_{attempt.id}'
    if request is not None and session_key in request.session:
        del request.session[session_key]


@login_required
def quiz_list(request):
    """Список доступных экзаменов"""
    categories = QuizCategory.objects.filter(is_active=True)

    # Администраторы (суперпользователи) имеют доступ ко всем экзаменам
    is_admin = request.user.is_superuser

    # Фильтруем экзамены: либо нет назначенных пользователей (доступен всем),
    # либо текущий пользователь в списке назначенных, либо пользователь - админ
    if is_admin:
        quiz_filter = Q(is_active=True)  # Админ видит все активные квизы
    else:
        quiz_filter = (Q(assigned_users__isnull=True) | Q(assigned_users=request.user)) & Q(is_active=True)

    # Все доступные квизы (без разделения на типы)
    all_quizzes = Quiz.objects.filter(quiz_filter).distinct()

    # Добавляем к каждой категории первый доступный quiz для тренировки
    categories_with_quiz = []
    for category in categories:
        # Находим первый квиз, который содержит эту категорию
        category_quiz = all_quizzes.filter(categories=category).first()
        category.quiz_for_training = category_quiz
        categories_with_quiz.append(category)

    # Статистика пользователя
    user_attempts = QuizAttempt.objects.filter(
        user=request.user,
        status=QuizAttempt.STATUS_COMPLETED
    ).select_related('quiz')

    context = {
        'categories': categories_with_quiz,
        'quizzes': all_quizzes,
        'user_attempts': user_attempts,
        'is_admin': is_admin,
    }

    return render(request, 'directory/quiz/quiz_list.html', context)


@login_required
def quiz_start(request, quiz_id, category_id=None):
    """Начало прохождения экзамена или тренировки по разделу

    Args:
        quiz_id: ID экзамена
        category_id: ID раздела (если это тренировка по разделу)
    """
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True)

    # Проверяем режим токена
    token_mode = request.session.get('quiz_token_mode', False)
    token_id = request.session.get('quiz_token_id')

    # Администраторы имеют доступ ко всем экзаменам
    is_admin = request.user.is_superuser

    # Если режим токена активен, проверяем соответствие токена и экзамена
    if token_mode and token_id:
        try:
            token = QuizAccessToken.objects.get(id=token_id)
            # Разрешаем основной экзамен токена
            is_main_quiz = token.quiz.id == quiz_id

            # Разрешаем тренировки по разделам, которые входят в экзамен токена
            is_allowed_training = False
            if category_id:
                # Получаем список разделов экзамена токена
                exam_categories = token.quiz.get_exam_categories()
                exam_category_ids = list(exam_categories.values_list('id', flat=True))
                # Проверяем, что раздел тренировки входит в экзамен
                is_allowed_training = int(category_id) in exam_category_ids

            if not (is_main_quiz or is_allowed_training):
                messages.error(request, 'Этот токен не предоставляет доступ к данному экзамену или тренировке.')
                return redirect('directory:quiz:exam_home')
        except QuizAccessToken.DoesNotExist:
            # Токен не найден, очищаем сессию
            request.session.pop('quiz_token_mode', None)
            request.session.pop('quiz_token_id', None)
            token_mode = False

    # Проверяем доступность экзамена для пользователя (если не режим токена и не админ)
    if not token_mode and not is_admin and not quiz.is_available_for_user(request.user):
        messages.error(request, 'У вас нет доступа к этому экзамену.')
        return redirect('directory:quiz:quiz_list')

    # Если указан category_id - тренировка по разделу
    if category_id:
        category = get_object_or_404(QuizCategory, id=category_id, is_active=True)

        # Проверяем, есть ли незавершенная попытка тренировки по ЭТОМУ разделу
        existing_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            category=category,
            status=QuizAttempt.STATUS_IN_PROGRESS
        ).first()

        if existing_attempt:
            # Продолжаем незавершенную тренировку
            answered_count = UserAnswer.objects.filter(attempt=existing_attempt).count()
            return redirect('directory:quiz:quiz_question',
                          attempt_id=existing_attempt.id,
                          question_number=answered_count + 1)

        # Проверяем, есть ли завершенная попытка по этому разделу
        completed_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            category=category,
            status=QuizAttempt.STATUS_COMPLETED
        ).first()

        if completed_attempt:
            # Сбрасываем завершенную тренировку - удаляем старую попытку
            completed_attempt.delete()

        # Создаем новую попытку тренировки
        questions = quiz.get_questions_for_category(category)

        if not questions:
            messages.error(request, f'В разделе "{category.name}" нет вопросов.')
            if token_mode:
                return redirect('directory:quiz:exam_home')
            return redirect('directory:quiz:quiz_list')

        attempt_kwargs = {
            'quiz': quiz,
            'user': request.user,
            'category': category,  # Указываем раздел для тренировки
            'total_questions': len(questions),
            'status': QuizAttempt.STATUS_IN_PROGRESS,
            'max_questions': len(questions),
            'time_limit_seconds': 0,  # Без лимита времени для тренировки
            'allowed_incorrect_answers': 0,  # Без лимита ошибок
        }

    else:
        # Итоговый экзамен (срез из всех разделов)
        # Проверяем, есть ли незавершенная попытка экзамена (category=None)
        existing_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            category__isnull=True,  # Только итоговые экзамены
            status=QuizAttempt.STATUS_IN_PROGRESS
        ).first()

        if existing_attempt:
            # НОВАЯ ЛОГИКА: при попытке начать новый экзамен - проваливаем незавершенный
            existing_attempt.status = QuizAttempt.STATUS_ABANDONED
            existing_attempt.failure_reason = QuizAttempt.FAILURE_NONE
            existing_attempt.completed_at = timezone.now()
            existing_attempt.save(update_fields=['status', 'failure_reason', 'completed_at'])
            existing_attempt.calculate_score()
            messages.warning(request, 'Предыдущая попытка экзамена была прервана.')
            # Продолжаем создание новой попытки ниже

        # Создаем новую попытку экзамена
        questions = quiz.get_questions_for_exam()

        if not questions:
            messages.error(request, 'В этом экзамене нет вопросов.')
            if token_mode:
                return redirect('directory:quiz:exam_home')
            return redirect('directory:quiz:quiz_list')

        attempt_kwargs = {
            'quiz': quiz,
            'user': request.user,
            'category': None,  # None = итоговый экзамен (не тренировка)
            'total_questions': len(questions),
            'status': QuizAttempt.STATUS_IN_PROGRESS,
            'max_questions': len(questions),
            'time_limit_seconds': quiz.exam_time_limit * 60,
            'allowed_incorrect_answers': quiz.exam_allowed_incorrect,
        }

    # Создаем попытку
    attempt = QuizAttempt.objects.create(**attempt_kwargs)

    # Сохраняем порядок вопросов в БД (для возможности возобновления)
    QuizQuestionOrder.objects.bulk_create([
        QuizQuestionOrder(attempt=attempt, question=q, order=i)
        for i, q in enumerate(questions)
    ])

    # Также сохраняем в сессии для обратной совместимости (legacy)
    request.session[f'quiz_questions_{attempt.id}'] = [q.id for q in questions]
    request.session.modified = True

    # Увеличиваем счетчик попыток
    quiz.attempts_count += 1
    quiz.save(update_fields=['attempts_count'])

    if category_id:
        messages.success(request, f'Тренировка по разделу "{category.name}" начата. Всего вопросов: {len(questions)}')
    else:
        messages.success(request, f'Экзамен "{quiz.title}" начат. Всего вопросов: {len(questions)}')

    return redirect('directory:quiz:quiz_question', attempt_id=attempt.id, question_number=1)


@login_required
def quiz_question(request, attempt_id, question_number):
    """Отображение вопроса"""
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        status=QuizAttempt.STATUS_IN_PROGRESS
    )

    time_left = _get_time_left_seconds(attempt)
    if time_left is not None and time_left <= 0:
        _finalize_attempt(attempt, request, QuizAttempt.FAILURE_TIMEOUT)
        messages.error(request, 'Время экзамена истекло.')
        return redirect('directory:quiz:quiz_result', attempt_id=attempt.id)

    # Получаем порядок вопросов из БД (приоритет) или из сессии (fallback)
    question_orders = QuizQuestionOrder.objects.filter(attempt=attempt).order_by('order')

    if question_orders.exists():
        # Загружаем из БД
        question_ids = [qo.question_id for qo in question_orders]
    else:
        # Fallback на сессию (для старых попыток)
        question_ids = request.session.get(f'quiz_questions_{attempt.id}')
        if not question_ids:
            messages.error(request, 'Не удалось загрузить вопросы. Начните экзамен заново.')
            # В токен-режиме возвращаем на exam_home
            token_mode = request.session.get('quiz_token_mode', False)
            if token_mode:
                return redirect('directory:quiz:exam_home')
            return redirect('directory:quiz:quiz_list')

    # Проверяем номер вопроса
    if question_number < 1 or question_number > len(question_ids):
        return redirect('directory:quiz:quiz_result', attempt_id=attempt.id)

    question_id = question_ids[question_number - 1]
    question = get_object_or_404(Question, id=question_id)

    # Получаем варианты ответов и перемешиваем их случайным образом
    answers = list(question.answers.all())
    random.shuffle(answers)

    # Проверяем, был ли уже дан ответ на этот вопрос
    user_answer = UserAnswer.objects.filter(
        attempt=attempt,
        question=question
    ).first()

    # Подсчитываем статистику
    answered_count = UserAnswer.objects.filter(attempt=attempt).count()
    skipped_count = UserAnswer.objects.filter(attempt=attempt, is_skipped=True).count()

    progress_percent = 0
    if question_ids:
        progress_percent = int((question_number / len(question_ids)) * 100)

    allowed_incorrect = attempt.allowed_incorrect_answers
    remaining_incorrect = None
    if allowed_incorrect:
        remaining_incorrect = max(0, allowed_incorrect - attempt.incorrect_answers)

    time_left_display = None
    if time_left is not None:
        minutes, seconds = divmod(time_left, 60)
        time_left_display = f"{minutes:02d}:{seconds:02d}"

    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'question': question,
        'answers': answers,
        'question_number': question_number,
        'total_questions': len(question_ids),
        'progress_percent': progress_percent,
        'answered_count': answered_count,
        'skipped_count': skipped_count,
        'user_answer': user_answer,
        'show_correct_answer': attempt.quiz.show_correct_answer,
        'allow_skip': attempt.quiz.allow_skip,
        'time_left_seconds': time_left,
        'time_left_display': time_left_display,
        'allowed_incorrect': allowed_incorrect,
        'incorrect_answers': attempt.incorrect_answers,
        'remaining_incorrect': remaining_incorrect,
        'result_url': reverse('directory:quiz:quiz_result', kwargs={'attempt_id': attempt.id}),
    }

    return render(request, 'directory/quiz/quiz_question.html', context)


@login_required
@require_POST
def quiz_answer(request, attempt_id, question_id):
    """Обработка ответа на вопрос"""
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user,
        status=QuizAttempt.STATUS_IN_PROGRESS
    )

    time_left = _get_time_left_seconds(attempt)
    result_url = reverse('directory:quiz:quiz_result', kwargs={'attempt_id': attempt.id})

    if time_left is not None and time_left <= 0:
        _finalize_attempt(attempt, request, QuizAttempt.FAILURE_TIMEOUT)
        return JsonResponse({
            'success': True,
            'finished': True,
            'reason': 'timeout',
            'redirect': result_url
        })

    question = get_object_or_404(Question, id=question_id)
    answer_id = request.POST.get('answer_id')
    skip = request.POST.get('skip') == 'true'

    # Проверяем, не был ли уже дан ответ
    existing_answer = UserAnswer.objects.filter(
        attempt=attempt,
        question=question
    ).first()

    if existing_answer:
        # Уже отвечали на этот вопрос
        question_ids = request.session.get(f'quiz_questions_{attempt.id}', [])
        current_index = question_ids.index(question_id)
        next_question = current_index + 2  # +1 для индекса, +1 для следующего

        if next_question <= len(question_ids):
            return JsonResponse({
                'success': True,
                'already_answered': True,
                'next_url': reverse('directory:quiz:quiz_question', kwargs={'attempt_id': attempt.id, 'question_number': next_question})
            })
        else:
            return JsonResponse({
                'success': True,
                'already_answered': True,
                'next_url': result_url,
                'finished': True
            })

    if skip:
        # Пропуск вопроса - НЕ считается ошибкой
        user_answer = UserAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_answer=None,
            is_correct=False,
            is_skipped=True
        )
        attempt.skipped_questions += 1
        attempt.save(update_fields=['skipped_questions'])

        # Пропущенные вопросы НЕ проверяются на лимит ошибок
        limit_reached = False

        if limit_reached:
            _finalize_attempt(attempt, request, QuizAttempt.FAILURE_INCORRECT)
            return JsonResponse({
                'success': True,
                'skipped': True,
                'finished': True,
                'reason': 'incorrect_limit',
                'redirect': result_url
            })

        question_ids = request.session.get(f'quiz_questions_{attempt.id}', [])
        current_index = question_ids.index(question_id)
        next_question = current_index + 2
        if next_question <= len(question_ids):
            next_url = reverse('directory:quiz:quiz_question', kwargs={'attempt_id': attempt.id, 'question_number': next_question})
        else:
            # Дошли до конца - проверяем пропущенные
            first_skipped = _find_first_skipped_question(attempt)
            if first_skipped:
                next_url = reverse('directory:quiz:quiz_question', kwargs={'attempt_id': attempt.id, 'question_number': first_skipped})
            else:
                _finalize_attempt(attempt, request)
                next_url = result_url

        return JsonResponse({
            'success': True,
            'skipped': True,
            'next_url': next_url,
            'finished': next_url == result_url,
            'incorrect_answers': attempt.incorrect_answers,
            'allowed_incorrect': attempt.allowed_incorrect_answers,
            'time_left_seconds': _get_time_left_seconds(attempt),
        })

    # Обработка ответа
    if not answer_id:
        return JsonResponse({
            'success': False,
            'error': 'Выберите ответ'
        }, status=400)

    answer = get_object_or_404(Answer, id=answer_id, question=question)
    is_correct = answer.is_correct

    # Сохраняем ответ
    user_answer = UserAnswer.objects.create(
        attempt=attempt,
        question=question,
        selected_answer=answer,
        is_correct=is_correct,
        is_skipped=False
    )

    # Обновляем статистику попытки
    if is_correct:
        attempt.correct_answers += 1
        attempt.save(update_fields=['correct_answers'])
    else:
        attempt.incorrect_answers += 1
        attempt.save(update_fields=['incorrect_answers'])

    # Получаем правильный ответ для отображения
    correct_answer = question.get_correct_answer()

    # Определяем, есть ли еще вопросы
    question_ids = request.session.get(f'quiz_questions_{attempt.id}', [])
    current_index = question_ids.index(question_id)
    has_next = current_index < len(question_ids) - 1

    # НОВАЯ ЛОГИКА: НЕ завершаем экзамен при достижении лимита ошибок
    # Даём пользователю ответить на все вопросы, а в результатах покажем провал

    if not has_next:
        # Дошли до конца списка вопросов - проверяем, есть ли пропущенные
        first_skipped = _find_first_skipped_question(attempt)
        if first_skipped:
            # Есть пропущенные - отправляем на первый пропущенный
            next_url = reverse('directory:quiz:quiz_question', kwargs={'attempt_id': attempt.id, 'question_number': first_skipped})
        else:
            # Все вопросы отвечены - завершаем
            _finalize_attempt(attempt, request)
            next_url = result_url
    else:
        next_url = reverse('directory:quiz:quiz_question', kwargs={'attempt_id': attempt.id, 'question_number': current_index + 2})

    response_data = {
        'success': True,
        'is_correct': is_correct,
        'correct_answer_id': correct_answer.id if correct_answer else None,
        'explanation': question.explanation if question.explanation else None,
        'has_next': has_next,
        'show_correct_answer': attempt.quiz.show_correct_answer,
        'next_url': next_url,
        'finished': not has_next,
        'incorrect_answers': attempt.incorrect_answers,
        'allowed_incorrect': attempt.allowed_incorrect_answers,
        'time_left_seconds': _get_time_left_seconds(attempt),
    }

    return JsonResponse(response_data)


@login_required
def quiz_result(request, attempt_id):
    """Результаты прохождения экзамена"""
    attempt = get_object_or_404(
        QuizAttempt,
        id=attempt_id,
        user=request.user
    )

    # Если попытка еще не завершена, завершаем ее
    if attempt.status == QuizAttempt.STATUS_IN_PROGRESS:
        failure_reason = attempt.failure_reason or QuizAttempt.FAILURE_NONE
        _finalize_attempt(attempt, request, failure_reason)

    # НЕ очищаем режим токена - пользователь должен иметь возможность
    # вернуться на exam_home для повторной попытки или просмотра других разделов
    # Токен-режим остается активным до выхода из браузера или истечения сессии

    # Получаем детали ответов
    user_answers = UserAnswer.objects.filter(attempt=attempt).select_related(
        'question', 'selected_answer'
    ).order_by('answered_at')

    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'user_answers': user_answers,
    }

    return render(request, 'directory/quiz/quiz_result.html', context)


@login_required
def quiz_history(request):
    """История прохождения экзаменов пользователя"""
    attempts = QuizAttempt.objects.filter(
        user=request.user
    ).select_related('quiz').order_by('-started_at')

    context = {
        'attempts': attempts,
    }

    return render(request, 'directory/quiz/quiz_history.html', context)


@login_required
def category_detail(request, category_id):
    """Детали категории с вопросами"""
    category = get_object_or_404(QuizCategory, id=category_id, is_active=True)
    questions = Question.objects.filter(
        category=category,
        is_active=True
    ).order_by('order')

    # Администраторы (суперпользователи) имеют доступ ко всем экзаменам
    is_admin = request.user.is_superuser

    # Экзамены, которые включают этот раздел
    if is_admin:
        quizzes = Quiz.objects.filter(
            categories=category,
            is_active=True
        )
    else:
        # Для обычных пользователей - только назначенные или общедоступные
        quiz_filter = Q(assigned_users__isnull=True) | Q(assigned_users=request.user)
        quizzes = Quiz.objects.filter(
            quiz_filter,
            categories=category,
            is_active=True
        ).distinct()

    # Первый доступный квиз для тренировки
    quiz_for_training = quizzes.first()

    context = {
        'category': category,
        'questions': questions,
        'quizzes': quizzes,
        'quiz_for_training': quiz_for_training,
    }

    return render(request, 'directory/quiz/category_detail.html', context)


@login_required
def exam_home(request):
    """Главная страница exam поддомена с тренировками и экзаменом"""
    # Проверяем токен-режим
    token_mode = request.session.get('quiz_token_mode', False)
    token_id = request.session.get('quiz_token_id')

    if not token_mode or not token_id:
        messages.error(request, 'Доступ запрещён. Используйте токен доступа.')
        return redirect('directory:auth:login')

    try:
        access_token = QuizAccessToken.objects.get(id=token_id)
    except QuizAccessToken.DoesNotExist:
        messages.error(request, 'Токен не найден.')
        return redirect('directory:auth:login')

    quiz = access_token.quiz

    # Получаем разделы, которые входят в экзамен
    categories = quiz.get_exam_categories()

    # Добавляем прогресс и попытки для каждого раздела
    categories_with_progress = []
    for category in categories:
        # УПРОЩЕННАЯ ЛОГИКА: используем поле category для определения тренировок
        # Ищем незавершенные попытки тренировок по этому разделу
        in_progress_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            category=category,  # Прямая фильтрация по разделу
            status=QuizAttempt.STATUS_IN_PROGRESS
        ).first()

        # Ищем последнюю завершенную попытку тренировки по этому разделу
        last_completed_attempt = QuizAttempt.objects.filter(
            quiz=quiz,
            user=request.user,
            category=category,  # Прямая фильтрация по разделу
            status=QuizAttempt.STATUS_COMPLETED
        ).order_by('-completed_at').first()

        # Формируем прогресс
        progress = None
        if in_progress_attempt:
            answered_count = UserAnswer.objects.filter(attempt=in_progress_attempt).count()
            progress = {
                'in_progress': True,
                'answered': answered_count,
                'total': in_progress_attempt.total_questions,
                'attempt_id': in_progress_attempt.id,
            }
        elif last_completed_attempt:
            progress = {
                'in_progress': False,
                'correct': last_completed_attempt.correct_answers,
                'total': last_completed_attempt.total_questions,
                'percentage': last_completed_attempt.score_percentage,
            }

        # Добавляем прогресс к объекту категории
        category.progress = progress

        # Очищаем описание от "Импортировано из"
        if category.description and category.description.startswith('Импортировано из'):
            category.clean_description = None
        else:
            category.clean_description = category.description

        categories_with_progress.append(category)

    # УПРОЩЕННАЯ ЛОГИКА: Итоговый экзамен = category is NULL
    # Проверяем, есть ли незавершённая попытка ИТОГОВОГО экзамена
    existing_exam_attempt = QuizAttempt.objects.filter(
        quiz=quiz,
        user=request.user,
        category__isnull=True,  # NULL = итоговый экзамен
        status=QuizAttempt.STATUS_IN_PROGRESS
    ).first()

    # Статистика пользователя по ИТОГОВОМУ экзамену
    completed_exam_attempts = QuizAttempt.objects.filter(
        quiz=quiz,
        user=request.user,
        category__isnull=True,  # NULL = итоговый экзамен
        status=QuizAttempt.STATUS_COMPLETED
    ).order_by('-completed_at')

    # Последняя попытка итогового экзамена
    last_exam_attempt = completed_exam_attempts.first() if completed_exam_attempts.exists() else None

    context = {
        'quiz': quiz,
        'categories': categories_with_progress,
        'existing_attempt': existing_exam_attempt,
        'last_attempt': last_exam_attempt,
        'completed_attempts_count': len(completed_exam_attempts),
        'access_token': access_token,
    }

    return render(request, 'directory/quiz/exam_home.html', context)


def token_access(request, token):
    """Доступ к экзамену по токену с обязательной авторизацией"""
    from django.http import HttpResponseForbidden

    access_token = get_object_or_404(QuizAccessToken, token=token)

    # Проверяем валидность токена
    is_valid, message = access_token.is_valid()

    # Если токен невалиден - сразу отказываем
    if not is_valid:
        # Возвращаем страницу с ошибкой без редиректа
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Доступ запрещен</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }}
                .error-container {{
                    background: white;
                    padding: 3rem;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    color: #dc3545;
                    margin: 0 0 1rem 0;
                    font-size: 1.8rem;
                }}
                p {{
                    color: #666;
                    font-size: 1.1rem;
                    line-height: 1.6;
                    margin: 0;
                }}
                .message {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-top: 1.5rem;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🔒</div>
                <h1>Доступ запрещен</h1>
                <p>Токен доступа к экзамену недействителен</p>
                <div class="message">{message}</div>
            </div>
        </body>
        </html>
        """
        return HttpResponseForbidden(html)

    # Если пользователь не авторизован - перенаправляем на страницу входа
    if not request.user.is_authenticated:
        # Сохраняем токен в сессии, чтобы после входа вернуться сюда
        request.session['pending_quiz_token'] = str(token)
        # Перенаправляем на страницу входа с параметром next
        login_url = reverse('directory:auth:login')
        return redirect(f'{login_url}?next={request.path}')

    # Проверяем, что авторизованный пользователь - это тот, кому предназначен токен
    is_admin = request.user.is_superuser

    if not is_admin and access_token.user != request.user:
        messages.error(request, 'Этот токен предназначен для другого пользователя.')
        html = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Доступ запрещен</title>
            <style>
                body {{
                    margin: 0;
                    padding: 0;
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    min-height: 100vh;
                }}
                .error-container {{
                    background: white;
                    padding: 3rem;
                    border-radius: 12px;
                    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                    text-align: center;
                    max-width: 500px;
                }}
                .error-icon {{
                    font-size: 4rem;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    color: #dc3545;
                    margin: 0 0 1rem 0;
                    font-size: 1.8rem;
                }}
                p {{
                    color: #666;
                    font-size: 1.1rem;
                    line-height: 1.6;
                    margin: 0;
                }}
                .message {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                    padding: 1rem;
                    border-radius: 8px;
                    margin-top: 1.5rem;
                    font-weight: 600;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-icon">🚫</div>
                <h1>Доступ запрещен</h1>
                <p>Этот токен предназначен для пользователя: <strong>{access_token.user.username}</strong></p>
                <div class="message">Вы авторизованы как: {request.user.username}</div>
            </div>
        </body>
        </html>
        """
        return HttpResponseForbidden(html)

    # Определяем целевого пользователя
    target_user = request.user

    # Ищем незавершённую попытку для этого пользователя и экзамена
    existing_attempt = QuizAttempt.objects.filter(
        quiz=access_token.quiz,
        user=target_user,
        status=QuizAttempt.STATUS_IN_PROGRESS
    ).first()

    # Сохраняем токен в сессии для ограничения доступа к навигации
    request.session['quiz_token_mode'] = True
    request.session['quiz_token_id'] = access_token.id
    request.session.modified = True

    if existing_attempt and access_token.allow_resume:
        # ВОЗОБНОВЛЕНИЕ - есть незавершенная попытка
        # Находим последний отвеченный вопрос
        answered_count = UserAnswer.objects.filter(attempt=existing_attempt).count()
        total_questions = QuizQuestionOrder.objects.filter(attempt=existing_attempt).count()

        if answered_count >= total_questions:
            # Все вопросы отвечены - перенаправляем на результаты
            messages.info(request, 'Вы уже завершили этот экзамен.')
            return redirect('directory:quiz:quiz_result', attempt_id=existing_attempt.id)

        # Есть незавершенная попытка - направляем на главную страницу
        messages.info(request, f'У вас есть незавершенная попытка. Вы можете продолжить с того места, где остановились.')
        return redirect('directory:quiz:exam_home')

    # НОВАЯ попытка - направляем на главную страницу
    # Отмечаем токен как использованный (только для обычных пользователей)
    if not is_admin and not access_token.is_used:
        access_token.mark_as_used()

    # Перенаправляем на главную страницу exam поддомена
    if is_admin:
        messages.info(request, f'[ADMIN] Доступ к экзамену "{access_token.quiz.title}" (токен: {access_token.user.username})')
    else:
        messages.success(request, f'Доступ к экзамену "{access_token.quiz.title}" предоставлен!')

    return redirect('directory:quiz:exam_home')
