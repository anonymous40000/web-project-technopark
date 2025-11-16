from django.conf import settings
from django.db import models
from django.urls import reverse


class QuestionQuerySet(models.QuerySet):
    def newest(self): return self.order_by('-created', '-id')
    def best(self): return self.order_by('-rating', '-created', '-id')
    def with_author(self): return self.select_related('author')
    def with_counters(self): return self.annotate(answers_count=models.Count('answers', distinct=True))
    def by_tag(self, tag_name): return self.filter(question_tags__tag__name__iexact=tag_name)
    def for_author(self, user): return self.filter(author=user, is_active=True)
    def with_tags(self): return self.prefetch_related('question_tags__tag')


class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def newest_simple(self):
        return self.get_queryset().with_author().newest()

    def newest_full(self):
        return self.get_queryset().with_author().with_counters().with_tags().newest()

    def best_simple(self):
        return self.get_queryset().with_author().best()

    def best_full(self):
        return self.get_queryset().with_author().with_counters().with_tags().best()

    def by_tag(self, name):
        return self.get_queryset().with_author().with_counters().with_tags().by_tag(name).newest()

    def detail_qs(self):
        return self.get_queryset().with_author().with_tags().prefetch_related(
            'answers__author',
            'answers__likes'
        )

    def for_author(self, user):
        return self.get_queryset().with_author().with_counters().with_tags().for_author(user).newest()


class Question(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='author_id', related_name='questions', verbose_name='Автор')
    name = models.CharField('Заголовок', max_length=255)
    text = models.TextField('Текст вопроса')
    rating = models.IntegerField('Рейтинг', default=0)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    updated = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активен', default=True)

    objects = QuestionManager()

    class Meta:
        db_table = 'Question'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['-rating', '-created']),
            models.Index(fields=['author']),
        ]
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return f'Вопрос #{self.pk}: {self.name}'

    def get_absolute_url(self):
        return reverse('questions:question_detail', args=[self.pk])

    def title_for_page(self):
        return f'{self.name} - OlegOverFlow'

    def short_text(self, limit=1000):
        return (self.text[:limit] + '...') if len(self.text) > limit else self.text


class Answer(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='answers', verbose_name='Вопрос')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='author_id', related_name='answers', verbose_name='Автор')
    is_correct = models.BooleanField('Правильный ответ', default=False)
    text = models.TextField('Текст ответа')
    rating = models.IntegerField('Рейтинг', default=0)
    created = models.DateTimeField('Дата создания', auto_now_add=True)
    updated = models.DateTimeField('Дата обновления', auto_now=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        db_table = 'Answer'
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
            models.Index(fields=['question']),
            models.Index(fields=['author']),
        ]
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'

    def __str__(self):
        return f'Ответ #{self.pk} к вопросу #{self.question_id}'

    def mark_correct(self):
        Answer.objects.filter(question_id=self.question_id, is_correct=True).update(is_correct=False)
        Answer.objects.filter(pk=self.pk).update(is_correct=True)

    def unmark_correct(self):
        Answer.objects.filter(pk=self.pk).update(is_correct=False)


class Tag(models.Model):
    name = models.CharField('Название', max_length=255, db_index=True)

    class Meta:
        db_table = 'Tag'
        indexes = [
            models.Index(fields=['name']),
        ]
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class QuestionTag(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='question_tags', verbose_name='Вопрос')
    tag = models.ForeignKey('questions.Tag', on_delete=models.CASCADE, db_column='tag_id', related_name='tag_questions', verbose_name='Тег')
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'QuestionTag'
        indexes = [
            models.Index(fields=['question']),
            models.Index(fields=['tag']),
        ]
        verbose_name = 'Тег вопроса'
        verbose_name_plural = 'Теги вопросов'

    def __str__(self):
        return f'Вопрос #{self.question_id} — тег #{self.tag_id}'


class QuestionLike(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='likes', verbose_name='Вопрос')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id', related_name='question_likes', verbose_name='Пользователь')
    is_liked = models.BooleanField('Нравится', default=False)
    value = models.IntegerField('Значение голоса', default=1)
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'QuestionLike'
        unique_together = (('question', 'user'),)
        indexes = [
            models.Index(fields=['question']),
            models.Index(fields=['user']),
        ]
        verbose_name = 'Голос за вопрос'
        verbose_name_plural = 'Голоса за вопросы'

    def __str__(self):
        return f'Голос за вопрос #{self.question_id} от пользователя #{self.user_id}: {self.value}'


class AnswerLike(models.Model):
    answer = models.ForeignKey('questions.Answer', on_delete=models.CASCADE, db_column='answer_id', related_name='likes', verbose_name='Ответ')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, db_column='user_id', related_name='answer_likes', verbose_name='Пользователь')
    is_liked = models.BooleanField('Нравится', default=True)
    value = models.IntegerField('Значение голоса', default=1)
    created = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        db_table = 'AnswerLike'
        unique_together = (('answer', 'user'),)
        indexes = [
            models.Index(fields=['answer']),
            models.Index(fields=['user']),
        ]
        verbose_name = 'Голос за ответ'
        verbose_name_plural = 'Голоса за ответы'

    def __str__(self):
        return f'Голос за ответ #{self.answer_id} от пользователя #{self.user_id}: {self.value}'
