from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, db_column='user_id', related_name='profile', verbose_name='Пользователь')
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=10000, null=True, blank=True)

    total_questions = models.PositiveIntegerField(default=0, verbose_name='Всего вопросов')
    total_answers = models.PositiveIntegerField(default=0, verbose_name='Всего ответов')
    total_activity = models.PositiveIntegerField(default=0, verbose_name='Общая активность')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'UserProfile'
        indexes = [
            models.Index(fields=['-total_activity']),
            models.Index(fields=['-total_questions']),
            models.Index(fields=['-total_answers']),
        ]
        verbose_name = 'Профиль пользователя'
        verbose_name_plural = 'Профили пользователей'

    def __str__(self):
        return f'Профиль {self.user.get_username()}'

    def update_activity(self):
        """Обновление статистики активности"""
        from questions.models import Question, Answer
        self.total_questions = Question.objects.filter(author=self.user, is_active=True).count()
        self.total_answers = Answer.objects.filter(author=self.user, is_active=True).count()
        self.total_activity = self.total_questions + self.total_answers
        self.save(update_fields=['total_questions', 'total_answers', 'total_activity'])
