import time
import jwt
import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction
from django.db.models import Count, F, OuterRef, Subquery, Exists, IntegerField
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from .models import Question, Answer, QuestionLike, AnswerLike, Tag, QuestionTag
from .forms import AskForm, AnswerForm


def centrifugo_publish(channel: str, data: dict) -> None:
    url = f"{settings.CENTRIFUGO_HTTP_URL}/api"  # Убрали /publish
    payload = {
        "method": "publish",  # Добавили метод
        "params": {
            "channel": channel,
            "data": data
        }
    }
    r = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": settings.CENTRIFUGO_API_KEY,
        },
        json=payload,  # Изменили структуру
        timeout=3,
    )
    r.raise_for_status()
    print(f"✅ Published to {channel}: {r.json()}")


@login_required
def centrifugo_token(request):
    payload = {
        "sub": str(request.user.id),
        "exp": int(time.time()) + 60 * 10,
        "channel_patterns": [
            {
                "pattern": "question:*",
                "allow": ["subscribe"]
            }
        ]
    }
    token = jwt.encode(payload, settings.CENTRIFUGO_JWT_SECRET, algorithm="HS256")
    return JsonResponse({"token": token})


def paginate(objects_list, request, per_page=20):
    paginator = Paginator(objects_list, per_page)
    page_number = request.GET.get("page", 1)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    return page_obj


def get_question_list_queryset(request):
    answers_count_sq = Answer.objects.filter(
        question=OuterRef("pk"),
        is_active=True
    ).values("question").annotate(cnt=Count("*")).values("cnt")

    qs = Question.objects.filter(is_active=True).select_related(
        "author", "author__profile"
    ).prefetch_related(
        "question_tags__tag"
    ).annotate(
        answers_count=Subquery(answers_count_sq, output_field=IntegerField())
    )

    if request.user.is_authenticated:
        liked_sq = QuestionLike.objects.filter(
            question=OuterRef("pk"),
            user=request.user
        )
        qs = qs.annotate(user_has_liked=Exists(liked_sq))

    return qs


def index(request):
    q = request.GET.get("q", "").strip()
    qs = get_question_list_queryset(request)

    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.order_by("-created", "-id")
    page_obj = paginate(qs, request, per_page=20)

    return render(request, "questions/index.html", {
        "questions": page_obj,
        "page_obj": page_obj,
        "search_query": q,
        "page_title": "New Questions",
    })


def hot_questions(request):
    qs = get_question_list_queryset(request)
    qs = qs.order_by("-rating", "-created", "-id")
    page_obj = paginate(qs, request, per_page=20)

    return render(request, "questions/hot.html", {
        "questions": page_obj,
        "page_obj": page_obj,
        "page_title": "Hot Questions",
    })


def tag_view(request, tag_name=None):
    tag = (tag_name or request.GET.get("tag", "")).strip()
    if not tag:
        return redirect("questions:index")

    q = request.GET.get("q", "").strip()

    qs = get_question_list_queryset(request).filter(
        question_tags__tag__name__iexact=tag
    )

    if q:
        qs = qs.filter(name__icontains=q)

    qs = qs.order_by("-created", "-id")
    page_obj = paginate(qs, request, per_page=20)

    return render(request, "questions/tag.html", {
        "questions": page_obj,
        "page_obj": page_obj,
        "tag_name": tag,
        "search_query": q,
        "page_title": f"Tag: {tag}",
    })


def question_detail(request, question_id):
    question_qs = Question.objects.select_related(
        "author", "author__profile"
    ).prefetch_related("question_tags__tag")

    if request.user.is_authenticated:
        liked_sq = QuestionLike.objects.filter(question=OuterRef("pk"), user=request.user)
        question_qs = question_qs.annotate(user_has_liked=Exists(liked_sq))

    question = get_object_or_404(question_qs, pk=question_id, is_active=True)

    answers_qs = Answer.objects.filter(
        question=question,
        is_active=True
    ).select_related(
        "author", "author__profile"
    ).order_by("-is_correct", "-rating", "-created")

    if request.user.is_authenticated:
        ans_liked_sq = AnswerLike.objects.filter(answer=OuterRef("pk"), user=request.user)
        answers_qs = answers_qs.annotate(user_has_liked=Exists(ans_liked_sq))

    page_obj = paginate(answers_qs, request, per_page=30)

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Войдите, чтобы оставить ответ")
            return redirect("core:login")

        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.author = request.user
            answer.save()

            avatar_url = ""
            if hasattr(answer.author, "profile"):
                avatar_url = str(getattr(answer.author.profile, "get_avatar_url", "") or "")

            vote_url = reverse("questions:vote_answer", args=[question.id, answer.id])

            data = {
                "type": "new_answer",
                "question_id": question.id,
                "answer": {
                    "id": int(answer.id),
                    "text": str(answer.text),
                    "rating": int(answer.rating),
                    "is_correct": bool(answer.is_correct),
                    "created": str(answer.created),
                    "author": {
                        "username": str(answer.author.username),
                        "avatar_url": avatar_url,
                    },
                    "vote_url": str(vote_url),
                },
            }

            centrifugo_publish(f"question:{question.id}", data)

            messages.success(request, "Ответ добавлен")
            return redirect("questions:question_detail", question_id=question.pk)
    else:
        form = AnswerForm()

    return render(request, "questions/question.html", {
        "question": question,
        "answers": page_obj,
        "page_obj": page_obj,
        "form": form,
        "CENTRIFUGO_WS_URL": getattr(settings, "CENTRIFUGO_WS_URL", "ws://localhost:8001/connection/websocket"),
    })


@login_required
def ask_view(request):
    if request.method == "POST":
        form = AskForm(request.POST)
        if form.is_valid():
            question = form.save(commit=True, author=request.user)

            tags_list = form.cleaned_data.get("tags_input", [])
            for tag_name in tags_list:
                tag, _ = Tag.objects.get_or_create(name=tag_name)
                QuestionTag.objects.get_or_create(question=question, tag=tag)

            messages.success(request, "Вопрос создан")
            return redirect("questions:question_detail", question_id=question.pk)
    else:
        form = AskForm()

    return render(request, "questions/ask.html", {"form": form})


@login_required
def vote_question(request, question_id):
    if request.method != "POST" or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=400)

    question = get_object_or_404(Question, pk=question_id, is_active=True)
    try:
        new_rating = int(request.POST.get("rating", "0"))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid rating"}, status=400)

    if new_rating not in (-1, 0, 1):
        new_rating = 0

    with transaction.atomic():
        like, created = QuestionLike.objects.get_or_create(
            question=question, user=request.user, defaults={"value": 0}
        )
        delta = new_rating - like.value
        like.value = new_rating
        like.is_liked = (new_rating > 0)
        like.save()

        Question.objects.filter(pk=question.pk).update(rating=F("rating") + delta)
        question.refresh_from_db()

    return JsonResponse({"ok": True, "rating": question.rating, "user_vote": like.value})


@login_required
def vote_answer(request, question_id, answer_id):
    if request.method != "POST" or request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"ok": False, "error": "Invalid request"}, status=400)

    answer = get_object_or_404(Answer, pk=answer_id, question_id=question_id, is_active=True)
    try:
        new_rating = int(request.POST.get("rating", "0"))
    except ValueError:
        return JsonResponse({"ok": False, "error": "Invalid rating"}, status=400)

    if new_rating not in (-1, 0, 1):
        new_rating = 0

    with transaction.atomic():
        like, created = AnswerLike.objects.get_or_create(
            answer=answer, user=request.user, defaults={"value": 0}
        )
        delta = new_rating - like.value
        like.value = new_rating
        like.is_liked = (new_rating > 0)
        like.save()

        Answer.objects.filter(pk=answer.pk).update(rating=F("rating") + delta)
        answer.refresh_from_db()

    return JsonResponse({"ok": True, "rating": answer.rating, "user_vote": like.value})


@login_required
def mark_answer_correct(request, question_id, answer_id):
    question = get_object_or_404(Question, pk=question_id, author=request.user)
    answer = get_object_or_404(Answer, pk=answer_id, question=question)
    answer.mark_correct()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("questions:question_detail", question_id=question_id)


@login_required
def unmark_answer_correct(request, question_id, answer_id):
    question = get_object_or_404(Question, pk=question_id, author=request.user)
    answer = get_object_or_404(Answer, pk=answer_id, question=question)
    answer.unmark_correct()
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"ok": True})
    return redirect("questions:question_detail", question_id=question_id)
