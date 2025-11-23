import importlib
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.core.cache import cache
from django.db.models import Q, Count

from .models import Question, Answer
from core.views import sidebar_ctx
from .forms import AskForm, AnswerForm


User = None

auth_module = importlib.import_module('django.contrib.auth')
User = auth_module.get_user_model()


def paginate(objects_list, request, per_page=10, cache_timeout=30):
    page_number = request.GET.get('page', 1)

    cache_key = f"paginate_ids_{objects_list.model._meta.db_table}_{per_page}_{hash(str(objects_list.query))}"
    id_list = cache.get(cache_key)
    if id_list is None:
        id_list = list(objects_list.values_list('id', flat=True))
        cache.set(cache_key, id_list, cache_timeout)

    paginator = Paginator(id_list, per_page)
    try:
        page = paginator.page(page_number)
    except PageNotAnInteger:
        page = paginator.page(1)
    except EmptyPage:
        page = paginator.page(paginator.num_pages)

    page_objects = objects_list.filter(id__in=page.object_list)

    page.object_list = page_objects
    return page

def index(request, *args, **kwargs):
    search_query = request.GET.get('q', '').strip()
    tag_name = request.GET.get('tag', '').strip() if not search_query else None

    base_qs = Question.objects.detail_qs().annotate(
        answers_count=Count('answers')
    )

    if search_query:
        qs = base_qs.filter(
            Q(name__icontains=search_query) | Q(text__icontains=search_query)
        )
        page_title = f'Search: "{search_query}"'
    elif tag_name:
        qs = Question.objects.by_tag(tag_name)
        page_title = f'Tag: {tag_name}'
    else:
        qs = Question.objects.newest_full()
        page_title = "New Questions"

    page = paginate(qs, request, per_page=4)
    return render(request, 'questions/index.html', {
        "questions": page,
        "page_title": page_title,
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

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Нужно войти, чтобы отвечать.')
            return redirect('core:login')

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()
            cache.delete(cache_key)
            messages.success(request, 'Ваш ответ добавлен!')

            url = reverse('questions:question_detail', kwargs={'question_id': question.id}) + f'#answer-{answer.id}'
            return redirect(url)
    else:
        form = AnswerForm()

    return render(request, 'questions/question.html', {
        'question': question,
        'form': form,
        **sidebar_ctx(),
    })



def ask_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        messages.error(request, 'Нужно войти, чтобы задавать вопросы.')
        return redirect('core:login')

    if request.method == 'POST':
        form = AskForm(request.POST)
        if form.is_valid():
            question = form.save(commit=True, author=request.user)
            messages.success(request, 'Вопрос успешно создан!')
            return redirect('questions:question_detail', question_id=question.pk)
    else:
        form = AskForm()

    ctx = {'form': form}
    ctx.update(sidebar_ctx())
    return render(request, 'questions/ask.html', ctx)


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
