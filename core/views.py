from types import SimpleNamespace
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Count, Sum, F, Value
from django.db.models.functions import Coalesce

from core.models import UserProfile
from questions.models import Tag

User = get_user_model()

def sidebar_ctx():
    popular_tags = (
        Tag.objects.annotate(q_count=Count('tag_questions'))
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

        if not username or not password1 or password1 != password2 or not password2:
            messages.error(request, 'Please check username and passwords.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(username=username, email=email, password=password1)
            profile, _ = UserProfile.objects.get_or_create(user=user)
            if nickname:
                profile.username = nickname
            if email:
                profile.email = email
            if avatar:
                profile.profile_pic = avatar
            profile.save()
            login(request, user)
            return redirect('questions:index')

    ctx = {}
    ctx.update(sidebar_ctx())
    return render(request, 'core/register.html', ctx)


def settings_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        profile = request.user.profile
    else:
        profile = SimpleNamespace(username='', email='', bio='', profile_pic=None)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Нужно войти, чтобы сохранять настройки.')
            return redirect('core:login')
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        bio = request.POST.get('bio', '').strip()
        avatar = request.FILES.get('avatar')
        if username:
            profile.username = username
        if email:
            profile.email = email
        profile.bio = bio
        if avatar:
            profile.profile_pic = avatar
        profile.save()
        messages.success(request, 'Profile updated.')
        return redirect('core:settings')

    ctx = {'profile': profile}
    ctx.update(sidebar_ctx())
    return render(request, 'core/settings.html', ctx)



