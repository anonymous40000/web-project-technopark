from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('settings/', views.settings_view, name='settings')
]