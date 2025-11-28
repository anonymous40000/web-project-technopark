from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import get_user_model,login
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth import logout

from questions.models import Tag, Question, Answer
from .forms import LoginForm, RegistrationForm, SettingsForm

User = get_user_model()

def sidebar_ctx():
    cache_key = 'sidebar_data_v4'
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data

    try:
        popular_tags = (
            Tag.objects
               .annotate(q_count=Count('tag_questions', distinct=True))
               .order_by('-q_count')[:10]
        )

        best_members = (
            User.objects
                .select_related('profile')
                .filter(profile__is_active=True)
                .order_by('-profile__total_activity')[:10]
        )

        if not best_members:
            best_members = (
                User.objects
                    .select_related('profile')
                    .filter(is_active=True)
                    .order_by('-date_joined')[:10]
            )

        if not best_members:
            best_members = User.objects.select_related('profile').all()[:10]

        data = {
            'popular_tags': list(popular_tags),
            'best_members': list(best_members),
        }

        cache.set(cache_key, data, 300)

        return data
    except Exception as e:
        print(f"Error in sidebar_ctx: {e}")

        return {
            'popular_tags': [],
            'best_members': User.objects.select_related('profile').filter(is_active=True)[:5],
        }

def logout_view(request):
    logout(request)
    return redirect('questions:index')


def login_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('questions:index')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            login(request, user)
            next_url = request.POST.get('next') or reverse('questions:index')
            messages.success(request, f'Добро пожаловать, {user.username}!')
            return redirect(next_url)
    else:
        form = LoginForm()

    ctx = {'form': form}
    ctx.update(sidebar_ctx())
    return render(request, 'core/login.html', ctx)


def register_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('questions:index')

    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Аккаунт успешно создан! Добро пожаловать, {user.username}!')
            return redirect('questions:index')

    else:
        form = RegistrationForm()

    ctx = {
        'form': form,
    }
    ctx.update(sidebar_ctx())
    return render(request, 'core/register.html', ctx)



def settings_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        messages.error(request, 'Нужно войти, чтобы сохранять настройки.')
        return redirect('core:login')

    if request.method == 'POST':
        form = SettingsForm(request.POST, request.FILES, instance=request.user.profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Настройки успешно обновлены!')
            return redirect('core:settings')
    else:
        form = SettingsForm(instance=request.user.profile, user=request.user)

    ctx = {
        'form': form,
    }
    ctx.update(sidebar_ctx())
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
    ctx.update(sidebar_ctx())
    return render(request, 'core/member_detail.html', ctx)
