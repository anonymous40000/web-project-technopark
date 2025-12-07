from django.urls import path
from . import views

app_name = 'questions'

urlpatterns = [
    path('', views.index, name='index'),
    path('hot/', views.hot_questions, name='hot'),
    path('ask/', views.ask_view, name='ask'),
    path('<int:question_id>/', views.question_detail, name='question_detail'),
    path('tag/', views.tag_view, name='tag'),
    path('tag/<str:tag_name>/', views.tag_view, name='tag'),
    path('<int:question_id>/answers/<int:answer_id>/mark-correct/', views.mark_answer_correct, name="mark_answer_correct"),
    path('<int:question_id>/answers/<int:answer_id>/unmark-correct/', views.unmark_answer_correct, name="unmark_answer_correct"),
    path('search/', views.index, name='search'),
    path('question/<int:question_id>/vote/', views.vote_question, name='vote_question',),
    path('question/<int:question_id>/answer/<int:answer_id>/vote/', views.vote_answer, name='vote_answer',),
]
