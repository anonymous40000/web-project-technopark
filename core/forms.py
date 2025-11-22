from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label="Email", help_text="Введите действующий email")
    avatar = forms.ImageField(required=False, label="Аватар профиля")

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {
            'username': 'Логин',
        }
        help_texts = {
            'username': 'Придумайте уникальный логин',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            try:
                UserProfile.objects.create(
                    user=user,
                    profile_pic=self.cleaned_data.get('avatar')
                )
            except Exception as e:
                print("ERROR creating UserProfile:", e)
                raise
        return user


class LoginForm(forms.Form):
    login = forms.CharField(max_length=255, label="Логин или Email")
    password = forms.CharField(widget=forms.PasswordInput, label="Пароль")

    def clean(self):
        cleaned_data = super().clean()
        login = cleaned_data.get('login')
        password = cleaned_data.get('password')

        if login and password:
            user = authenticate(username=login, password=password)
            if user is None:
                try:
                    user_by_email = User.objects.get(email=login)
                    user = authenticate(username=user_by_email.username, password=password)
                except User.DoesNotExist:
                    pass

            if user is None:
                raise forms.ValidationError("Неверный логин или пароль")
            elif not user.is_active:
                raise forms.ValidationError("Аккаунт деактивирован")

            cleaned_data['user'] = user

        return cleaned_data


class SettingsForm(forms.ModelForm):
    username = forms.CharField(max_length=255, label="Имя пользователя")
    email = forms.EmailField(label="Email")

    class Meta:
        model = UserProfile
        fields = ['bio', 'profile_pic']
        labels = {
            'profile_pic': 'Аватар профиля',
            'bio': 'О себе'
        }
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if self.user:
            self.fields['username'].initial = self.user.username
            self.fields['email'].initial = self.user.email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if (self.user and
            User.objects.filter(username=username).exclude(pk=self.user.pk).exists()):
            raise forms.ValidationError("Пользователь с таким именем уже существует")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if (self.user and
            User.objects.filter(email=email).exclude(pk=self.user.pk).exists()):
            raise forms.ValidationError("Пользователь с таким email уже существует")
        return email

    def save(self, commit=True):
        if self.user:
            self.user.username = self.cleaned_data['username']
            self.user.email = self.cleaned_data['email']
            if commit:
                self.user.save()

        profile = super().save(commit=False)
        if commit:
            profile.save()
        return profile
