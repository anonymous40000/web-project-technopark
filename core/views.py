from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from questions.models import Question, Answer
from .forms import LoginForm, RegistrationForm, SettingsForm
from .models import UserProfile

User = get_user_model()


def logout_view(request):
    logout(request)
    return redirect('questions:index')


def login_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Already authenticated'}, status=400)
        return redirect('questions:index')

    next_url = request.GET.get('next') or request.POST.get('next') or reverse('questions:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                avatar_url = None
                if hasattr(user, 'profile'):
                    avatar_url = user.profile.get_avatar_url()
                return JsonResponse({
                    'ok': True,
                    'redirect_url': next_url,
                    'username': user.username,
                    'avatar_url': avatar_url,
                })
            return redirect(next_url)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False,
                    'errors': form.errors,
                }, status=400)
    else:
        form = LoginForm()

    ctx = {'form': form, 'next': next_url}
    return render(request, 'core/login.html', ctx)


def register_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'ok': False, 'error': 'Already authenticated'}, status=400)
        return redirect('questions:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'redirect_url': reverse('questions:index'),
                    'username': user.username,
                    'avatar_url': user.profile.get_avatar_url(),
                })
            return redirect('questions:index')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False,
                    'errors': form.errors,
                }, status=400)
    else:
        form = RegistrationForm()

    ctx = {'form': form}
    return render(request, 'core/register.html', ctx)


@login_required
def settings_view(request, *args, **kwargs):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            profile = form.save()

            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': True,
                    'username': request.user.username,
                    'email': request.user.email,
                    'avatar_url': profile.get_avatar_url(),
                })
            return redirect('core:settings')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'ok': False,
                    'errors': form.errors,
                }, status=400)
    else:
        form = SettingsForm(instance=profile, user=request.user)

    ctx = {'form': form}
    return render(request, 'core/settings.html', ctx)


def member_detail(request, pk, *args, **kwargs):
    member = get_object_or_404(
        User.objects.select_related('profile'),
        pk=pk,
    )

    questions = (
        Question.objects
                .filter(author=member, is_active=True)
                .select_related('author')
                .prefetch_related('question_tags__tag')
                .annotate(answers_count=Count('answers', distinct=True))
                .order_by('-created')[:10]
    )

    answers = (
        Answer.objects
              .filter(author=member, is_active=True)
              .select_related('question', 'question__author')
              .order_by('-created')[:10]
    )

    ctx = {
        'member': member,
        'questions': questions,
        'answers': answers,
    }
    return render(request, 'core/member_detail.html', ctx)
