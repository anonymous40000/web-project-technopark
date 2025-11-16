from django.core.cache import cache
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from core.models import UserProfile
from questions.models import Tag, Question, Answer

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


def login_view(request, *args, **kwargs):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or reverse('questions:index')
            return redirect(next_url)

        messages.error(request, 'Invalid login or password.')

    ctx = {}
    ctx.update(sidebar_ctx())
    return render(request, 'core/login.html', ctx)


def register_view(request, *args, **kwargs):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        nickname = request.POST.get('nickname', '').strip()
        avatar = request.FILES.get('avatar')

        if not username or not password1 or not password2 or password1 != password2:
            messages.error(request, 'Please check username and passwords.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
            )
            if nickname:
                user.first_name = nickname
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            if avatar:
                profile.profile_pic = avatar
                profile.save()

            login(request, user)
            return redirect('questions:index')

    ctx = {}
    ctx.update(sidebar_ctx())
    return render(request, 'core/register.html', ctx)


def settings_view(request, *args, **kwargs):
    if not request.user.is_authenticated:
        messages.error(request, 'Нужно войти, чтобы сохранять настройки.')
        return redirect('core:login')

    user = request.user
    profile, _ = UserProfile.objects.get_or_create(user=user)

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        bio = request.POST.get('bio', '').strip()
        avatar = request.FILES.get('avatar')

        if username:
            user.username = username
        if email:
            user.email = email
        user.save()

        profile.bio = bio
        if avatar:
            profile.profile_pic = avatar
        profile.save()

        messages.success(request, 'Profile updated.')
        return redirect('core:settings')

    ctx = {
        'profile': profile,
        'user_obj': user,
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
