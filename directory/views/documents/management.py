"""
📊 Представления для управления сгенерированными документами

Содержит представления для просмотра списка документов, 
деталей документа и скачивания документов.
"""
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.utils.translation import gettext as _

from directory.models import Employee
from directory.models.document_template import DocumentTemplate, GeneratedDocument


class GeneratedDocumentListView(LoginRequiredMixin, ListView):
    """
    Представление для списка сгенерированных документов
    """
    # Код из оригинального представления...


class GeneratedDocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Представление для просмотра деталей сгенерированного документа
    """
    # Код из оригинального представления...


def document_download(request, pk):
    """
    Функция для скачивания сгенерированного документа
    """
    # Код из оригинальной функции...