from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'username', 'email', 'is_active', 'created', 'updated')
    search_fields = ('user__username', 'user__email', 'username', 'email')
    list_filter = ('is_active',)
    readonly_fields = ('created', 'updated')
