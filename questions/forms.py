from django import forms
from .models import Question, Answer


class AskForm(forms.ModelForm):
    name = forms.CharField(
        label="Заголовок вопроса",
        min_length=10,
        error_messages={
            "required": "Введите заголовок вопроса",
            "min_length": "Заголовок должен содержать минимум 10 символов",
        },
    )

    text = forms.CharField(
        label="Текст вопроса",
        min_length=20,
        widget=forms.Textarea(attrs={"rows": 6}),
        error_messages={
            "required": "Введите текст вопроса",
            "min_length": "Описание должно содержать минимум 20 символов",
        },
    )

    tags_input = forms.CharField(
        label="Теги",
        help_text="Введите теги через запятую",
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "python, django, базы-данных"}),
    )

    class Meta:
        model = Question
        fields = ["name", "text", "tags_input"]

    def clean_tags_input(self):
        raw = (self.cleaned_data.get("tags_input") or "").strip()
        if not raw:
            return []

        tags = [t.strip() for t in raw.split(",") if t.strip()]
        if not tags:
            return []

        uniq = []
        seen = set()
        for t in tags:
            key = t.lower()
            if key not in seen:
                seen.add(key)
                uniq.append(t)

        return uniq

    def save(self, commit=True, author=None):
        question = super().save(commit=False)
        if author is not None:
            question.author = author
        if commit:
            question.save()
        return question


class AnswerForm(forms.ModelForm):
    text = forms.CharField(
        label="Содержание ответа",
        min_length=20,
        help_text="Введите содержание ответа",
        widget=forms.Textarea(attrs={"rows": 6, "placeholder": "Напишите ответ на вопрос..."}),
        error_messages={
            "required": "Введите текст ответа",
            "min_length": "Ответ должен содержать минимум 20 символов",
        },
    )

    class Meta:
        model = Answer
        fields = ["text"]
