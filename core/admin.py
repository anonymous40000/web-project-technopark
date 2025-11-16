from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'user_email', 'is_active', 'created', 'updated')
    search_fields = ('user__username', 'user__email')
    list_filter = ('is_active', 'created')
    readonly_fields = ('created', 'updated', 'total_questions', 'total_answers', 'total_activity')

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username'
    user_username.admin_order_field = 'user__username'

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
