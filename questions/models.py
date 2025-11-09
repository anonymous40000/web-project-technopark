from django.db import models
from django.urls import reverse

class QuestionQuerySet(models.QuerySet):
    def newest(self):
        return self.order_by('-created', '-id')
    def best(self):
        return self.order_by('-rating', '-created', '-id')
    def with_author(self):
        return self.select_related('author')
    def with_counters(self):
        return self.annotate(answers_count=models.Count('answers'))
    def by_tag(self, tag_name):
        return self.filter(question_tags__tag__name__iexact=tag_name)

class QuestionManager(models.Manager):
    def get_queryset(self):
        return QuestionQuerySet(self.model, using=self._db)

    def newest(self):
        return self.get_queryset().with_author().with_counters().newest()

    def best(self):
        return self.get_queryset().with_author().with_counters().best()

    def by_tag(self, name):
        return (self.get_queryset()
                    .with_author()
                    .with_counters()
                    .by_tag(name)
                    .newest())  

    def detail_qs(self):
        return self.get_queryset().with_author().prefetch_related('answers__author')


class Question(models.Model):
    author = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, db_column='author_id', related_name='questions')
    name = models.CharField(max_length=255)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    objects = QuestionManager()

    def get_absolute_url(self):
        return reverse('questions:detail', args=[self.pk])
    def title_for_page(self):
        return f'{self.name} - OlegOverFlow'
    def short_text(self, limit=1000):
        return (self.text[:limit] + '...') if len(self.text) > limit else self.text

    class Meta:
        db_table = 'Question'
        ordering = ['-created']

    def __str__(self):
        return f'Question#{self.pk}: {self.name}'

class Answer(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='answers')
    author = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, db_column='author_id', related_name='answers')
    is_correct = models.BooleanField(default=False)
    text = models.TextField()
    rating = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Answer'

    def __str__(self):
        return f'Answer#{self.pk} to Question#{self.question_id}'

    def mark_correct(self):
        Answer.objects.filter(question_id=self.question_id, is_correct=True).update(is_correct=False)
        Answer.objects.filter(pk=self.pk).update(is_correct=True)

    def unmark_correct(self):
        Answer.objects.filter(pk=self.pk).update(is_correct=False)

class Tag(models.Model):
    name = models.CharField(max_length=255)
    class Meta:
        db_table = 'Tag'
    def __str__(self):
        return self.name

class QuestionTag(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='question_tags')
    tag = models.ForeignKey('questions.Tag', on_delete=models.CASCADE, db_column='tag_id', related_name='tag_questions')
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'QuestionTag'
    def __str__(self):
        return f'Question#{self.question_id}-Tag#{self.tag_id}'

class QuestionLike(models.Model):
    question = models.ForeignKey('questions.Question', on_delete=models.CASCADE, db_column='question_id', related_name='likes')
    user = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, db_column='user_id', related_name='question_likes')
    is_liked = models.BooleanField(default=False)
    value = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'QuestionLike'
        unique_together = (('question', 'user'),)
    def __str__(self):
        return f'Question#{self.question_id} vote by User#{self.user_id}: {self.value}'

class AnswerLike(models.Model):
    answer = models.ForeignKey('questions.Answer', on_delete=models.CASCADE, db_column='answer_id', related_name='likes')
    user = models.ForeignKey('core.UserProfile', on_delete=models.CASCADE, db_column='user_id', related_name='answer_likes')
    is_liked = models.BooleanField(default=True)
    value = models.IntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'AnswerLike'
        unique_together = (('answer', 'user'),)
    def __str__(self):
        return f'Answer#{self.answer_id} vote by User#{self.user_id}: {self.value}'
