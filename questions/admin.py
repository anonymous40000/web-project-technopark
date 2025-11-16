from django.contrib import admin
from .models import (
    Question, Answer, Tag, QuestionTag, QuestionLike, AnswerLike
)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    fields = ('author', 'text', 'is_correct', 'rating', 'created', 'updated', 'is_active')
    readonly_fields = ('created', 'updated')

class QuestionTagInline(admin.TabularInline):
    model = QuestionTag
    extra = 0
    fields = ('tag', 'created')
    readonly_fields = ('created',)

class QuestionLikeInline(admin.TabularInline):
    model = QuestionLike
    extra = 0
    fields = ('user', 'is_liked', 'value', 'created')
    readonly_fields = ('created',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'rating', 'is_active', 'created', 'updated')
    list_filter = ('is_active', 'created', 'updated')
    search_fields = ('name', 'text', 'author__username', 'author__email')
    date_hierarchy = 'created'
    readonly_fields = ('created', 'updated')
    inlines = [AnswerInline, QuestionTagInline, QuestionLikeInline]
    ordering = ('-created',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'author', 'is_correct', 'rating', 'is_active', 'created', 'updated')
    list_filter = ('is_correct', 'is_active', 'created', 'updated')
    search_fields = ('text', 'author__username', 'author__email', 'question__name')
    readonly_fields = ('created', 'updated')
    ordering = ('-created',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(QuestionTag)
class QuestionTagAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'tag', 'created')
    search_fields = ('question__name', 'tag__name')
    readonly_fields = ('created',)


@admin.register(QuestionLike)
class QuestionLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'user', 'is_liked', 'value', 'created')
    list_filter = ('is_liked',)
    search_fields = ('question__name', 'user__username', 'user__email')
    readonly_fields = ('created',)


@admin.register(AnswerLike)
class AnswerLikeAdmin(admin.ModelAdmin):
    list_display = ('id', 'answer', 'user', 'is_liked', 'value', 'created')
    list_filter = ('is_liked',)
    search_fields = ('answer__question__name', 'user__username', 'user__email')
    readonly_fields = ('created',)
