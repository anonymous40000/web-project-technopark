from django import forms
from .models import Question, Tag, QuestionTag, Answer

class AskForm(forms.ModelForm):
    tags_input = forms.CharField(
        label="Теги",
        help_text="Введите теги через запятую",
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'python, django, базы-данных'})
    )

    class Meta:
        model = Question
        fields = ['name', 'text']
        labels = {
            'name': 'Заголовок вопроса',
            'text': 'Текст вопроса',
        }
        widgets = {
            'text': forms.Textarea(attrs={'rows': 6}),
        }

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 10:
            raise forms.ValidationError("Заголовок должен содержать минимум 10 символов")
        return name

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) < 20:
            raise forms.ValidationError("Описание должно содержать минимум 20 символов")
        return text

    def save(self, commit=True, author=None):
        question = super().save(commit=False)
        if author:
            question.author = author

        if commit:
            question.save()
            tags_input = self.cleaned_data.get('tags_input', '').strip()
            if tags_input:
                tags_list = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
                for tag_name in tags_list:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    QuestionTag.objects.get_or_create(question=question, tag=tag)
        return question


class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ['text']
        labels = {
            'text': 'Содержание ответа',
        }
        help_texts = {
            'text': 'Введите содержание ответа',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 6,
                'placeholder': 'Напишите ответ на вопрос...'
            }),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if len(text) < 20:
            raise forms.ValidationError("Ответ должен содержать минимум 20 символов")
        return text

    def save(self, commit=True):
        answer = super().save(commit=False)
        if commit:
            answer.save()
        return answer
