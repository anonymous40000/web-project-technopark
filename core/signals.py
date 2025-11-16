from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from django.contrib.auth import get_user_model

from questions.models import Question, Answer

User = get_user_model()

@receiver([post_save, post_delete], sender=Question)
@receiver([post_save, post_delete], sender=Answer)
def update_user_activity(sender, instance, **kwargs):
    if hasattr(instance, 'author'):
        user = instance.author
        if hasattr(user, 'profile') and user.profile:
            transaction.on_commit(lambda: update_profile_activity(user.profile))

def update_profile_activity(profile):
    try:
        profile.update_activity()
    except Exception as e:
        print(f"Error updating profile activity: {e}")
