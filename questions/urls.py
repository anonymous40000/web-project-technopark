from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('hot/', views.hot_questions, name='hot'), 
    path('ask/', views.ask_view, name='ask'),
    path('<int:question_id>/', views.question_detail, name='question_detail'),
    path('tag/', views.tag_view, name='tag'),
    path('tag/<str:tag_name>/', views.tag_view, name='tag'),
]

