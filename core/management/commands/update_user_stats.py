from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count
from core.models import UserProfile
from questions.models import Question, Answer

User = get_user_model()

class Command(BaseCommand):
    help = 'Updates activity statistics for all users'

    def handle(self, *args, **options):
        user_question_counts = Question.objects.filter(is_active=True).values('author_id').annotate(count=Count('id'))
        user_answer_counts = Answer.objects.filter(is_active=True).values('author_id').annotate(count=Count('id'))

        question_counts = {item['author_id']: item['count'] for item in user_question_counts}
        answer_counts = {item['author_id']: item['count'] for item in user_answer_counts}

        users = User.objects.all()
        total = users.count()
        updated = 0

        self.stdout.write(f'Updating statistics for {total} users...')

        for user in users:
            profile, created = UserProfile.objects.get_or_create(user=user)

            questions_count = question_counts.get(user.id, 0)
            answers_count = answer_counts.get(user.id, 0)

            profile.total_questions = questions_count
            profile.total_answers = answers_count
            profile.total_activity = questions_count + answers_count
            profile.save(update_fields=['total_questions', 'total_answers', 'total_activity'])

            updated += 1
            if updated % 10 == 0:
                self.stdout.write(f'Updated {updated}/{total} users...')

        self.stdout.write(self.style.SUCCESS(f'Successfully updated statistics for {updated} users'))
        self.stdout.write(self.style.SUCCESS('Sample data:'))

        sample_users = User.objects.select_related('profile').filter(profile__total_activity__gt=0)[:3]
        for user in sample_users:
            self.stdout.write(f'User: {user.username}, Questions: {user.profile.total_questions}, Answers: {user.profile.total_answers}, Total: {user.profile.total_activity}')
