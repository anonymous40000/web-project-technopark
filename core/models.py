from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, db_column='user_id', related_name='profile')
    username = models.CharField(max_length=255, blank=True)
    email = models.CharField(max_length=255, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', null=True, blank=True)
    bio = models.TextField(max_length=10000, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
