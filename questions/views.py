import importlib
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.cache import cache

from .models import Question, Answer
from core.views import sidebar_ctx


User = None

auth_module = importlib.import_module('django.contrib.auth')
User = auth_module.get_user_model()


def paginate(objects_list, request, per_page=10, cache_timeout=30):
    page_number = request.GET.get('page', 1)

    if hasattr(objects_list, 'model'):
        cache_key = f"paginate_{objects_list.model._meta.db_table}_{page_number}_{per_page}_{hash(str(objects_list.query))}"
        cached_page = cache.get(cache_key)

        if cached_page:
            return cached_page

        id_list = list(objects_list.values_list('id', flat=True))
        paginator = Paginator(id_list, per_page)

        try:
            page = paginator.page(page_number)
        except PageNotAnInteger:
            page = paginator.page(1)
        except EmptyPage:
            page = paginator.page(paginator.num_pages)

        current_ids = page.object_list
        page_objects = objects_list.model.objects.filter(id__in=current_ids)

        if hasattr(objects_list, '_prefetch_related_lookups'):
            page_objects = page_objects.prefetch_related(*objects_list._prefetch_related_lookups)
        if hasattr(objects_list, '_select_related'):
            page_objects = page_objects.select_related(*objects_list._select_related)
        if hasattr(objects_list, '_annotations'):
            for alias, annotation in objects_list._annotations.items():
                page_objects = page_objects.annotate(**{alias: annotation})

        page.object_list = page_objects.order_by('-created')
        page.paginator.count = len(id_list)

        cache.set(cache_key, page, cache_timeout)

        return page

    paginator = Paginator(objects_list, per_page)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


def index(request, *args, **kwargs):
    tag_name = request.GET.get('tag')
    qs = Question.objects.by_tag(tag_name) if tag_name else Question.objects.newest_full()
    page = paginate(qs, request, per_page=4)
    return render(request, 'questions/index.html', {
        "questions": page,
        "tag_name": tag_name,
        "page_title": "New Questions",
        **sidebar_ctx(),
    })


def tag_view(request, tag_name=None):
    tag_name = request.GET.get('tag', tag_name)
    qs = Question.objects.by_tag(tag_name)
    page = paginate(qs, request, per_page=5)
    return render(request, 'questions/tag.html', {
        'questions': page,
        'tag_name': tag_name,
        **sidebar_ctx(),
    })


def question_detail(request, question_id):
    cache_key = f'question_detail_{question_id}'
    question = cache.get(cache_key)

    if not question:
        question = get_object_or_404(Question.objects.detail_qs(), pk=question_id)
        cache.set(cache_key, question, 60)

    return render(request, 'questions/question.html', {
        'question': question,
        **sidebar_ctx(),
    })


def ask_view(request, *args, **kwargs):
    return render(request, 'questions/ask.html', {
        **sidebar_ctx(),
    })


def hot_questions(request):
    qs = Question.objects.best_full()
    page = paginate(qs, request, per_page=4)
    return render(request, 'questions/hot.html', {
        "questions": page,
        "page_title": "Hot Questions",
        **sidebar_ctx(),
    })


def _redirect_back_or_detail(request, question_pk: int):
    next_url = request.POST.get("next")
    return redirect(next_url) if next_url else redirect(reverse("questions:question_detail", args=[question_pk]))


@require_POST
def mark_answer_correct(request, question_id: int, answer_id: int):
    answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
    answer.mark_correct()

    cache_key = f'question_detail_{question_id}'
    cache.delete(cache_key)

    return _redirect_back_or_detail(request, answer.question_id)


@require_POST
def unmark_answer_correct(request, question_id: int, answer_id: int):
    answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
    answer.unmark_correct()

    cache_key = f'question_detail_{question_id}'
    cache.delete(cache_key)

    return _redirect_back_or_detail(request, answer.question_id)
