from django.shortcuts import render
from questions.views import POPULAR_TAGS, BEST_MEMBERS

def login_view(request, *args, **kwargs):
    return render(request, 'core/login.html', {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS
    })

def register_view(request, *args, **kwargs):
    return render(request, 'core/register.html', {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS
    })

def settings_view(request, *args, **kwargs):
    return render(request, 'core/settings.html', {
        'popular_tags': POPULAR_TAGS,
        'best_members': BEST_MEMBERS
    })