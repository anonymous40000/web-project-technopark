from django.db.models import Count, Sum, F, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Question, Answer, Tag
from core.models import UserProfile


def paginate(objects_list, request, per_page=10):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get('page', 1)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)
    return page


def sidebar_ctx():
    popular_tags = (
        Tag.objects
           .annotate(q_count=Count('tag_questions'))
           .order_by('-q_count')[:10]
    )
    best_members = (
        UserProfile.objects
           .annotate(q_sum=Coalesce(Sum('questions__rating'), Value(0)))
           .annotate(a_sum=Coalesce(Sum('answers__rating'),  Value(0)))
           .annotate(total=F('q_sum') + F('a_sum'))
           .order_by('-total')[:10]
    )
    return {'popular_tags': popular_tags, 'best_members': best_members}


def index(request, *args, **kwargs):
    tag_name = request.GET.get('tag')
    qs = Question.objects.by_tag(tag_name) if tag_name else Question.objects.newest()
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
    question = get_object_or_404(Question.objects.detail_qs(), pk=question_id)
    return render(request, 'questions/question.html', {
        'question': question,
        **sidebar_ctx(),
    })


def ask_view(request, *args, **kwargs):
    return render(request, 'questions/ask.html', {
        **sidebar_ctx(),
    })


def hot_questions(request):
    qs = Question.objects.best()
    page = paginate(qs, request, per_page=4)
    return render(request, 'questions/hot.html', {
        "questions": page,
        "page_title": "Hot Questions",
        **sidebar_ctx(),
    })


def _redirect_back_or_detail(request, question_pk: int):
    next_url = request.POST.get("next")
    return redirect(next_url) if next_url else redirect(reverse("questions:detail", args=[question_pk]))


@require_POST
def mark_answer_correct(request, question_id: int, answer_id: int):
    answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
    answer.mark_correct()
    return _redirect_back_or_detail(request, answer.question_id)


@require_POST
def unmark_answer_correct(request, question_id: int, answer_id: int):
    answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id)
    answer.unmark_correct()
    return _redirect_back_or_detail(request, answer.question_id)
