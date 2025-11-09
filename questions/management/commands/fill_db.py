import math
import random
import string
from collections import defaultdict

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import Value
from django.utils import timezone

from core.models import UserProfile
from questions.models import (
    Question, Answer, Tag, QuestionTag,
    QuestionLike, AnswerLike
)


def rand_word(n=8):
    return ''.join(random.choices(string.ascii_lowercase, k=n))


def chunked(iterable, size):
    for i in range(0, len(iterable), size):
        yield iterable[i:i+size]


class Command(BaseCommand):
    help = "Fill database with test data. Usage: python manage.py fill_db <ratio>"

    def add_arguments(self, parser):
        parser.add_argument('ratio', type=int, help='Base factor. users=ratio; questions=10*ratio; answers=100*ratio; tags=ratio; votes=200*ratio')
        parser.add_argument('--batch', type=int, default=5000, help='bulk_create batch size (default 5000)')
        parser.add_argument('--password', default='TestPass123!', help='password for all generated users (hashed once)')
        parser.add_argument('--seed', type=int, default=42, help='random seed for reproducibility')

    @transaction.atomic
    def handle(self, *args, **opts):
        ratio = opts['ratio']
        if ratio <= 0:
            raise CommandError('ratio must be positive integer')

        random.seed(opts['seed'])

        n_users     = ratio
        n_questions = ratio * 10
        n_answers   = ratio * 100
        n_tags      = ratio
        n_votes     = ratio * 200  

        batch_size = max(500, int(opts['batch']))
        password_hash = make_password(opts['password'])

        User = get_user_model()

        self.stdout.write(self.style.SUCCESS(f'Filling DB with ratio={ratio} (batch={batch_size})'))
        self.stdout.write(self.style.NOTICE(f'Users={n_users}, Questions={n_questions}, Answers={n_answers}, Tags={n_tags}, Votes={n_votes}'))

        existing_users = User.objects.count()
        users_to_create = n_users
        user_objs = []
        for i in range(users_to_create):
            uname = f'user_{rand_word(6)}_{i}'
            email = f'{uname}@example.com'
            user_objs.append(User(username=uname, email=email, password=password_hash, is_active=True))
        for chunk in chunked(user_objs, batch_size):
            User.objects.bulk_create(chunk, batch_size=batch_size, ignore_conflicts=True)

        user_ids = list(User.objects.order_by('id').values_list('id', flat=True))
        if len(user_ids) < n_users:
            user_ids = user_ids[:n_users]

        existing_profiles = set(UserProfile.objects.values_list('user_id', flat=True))
        profile_objs = []
        for uid in user_ids:
            if uid in existing_profiles:
                continue
            profile_objs.append(UserProfile(
                user_id=uid,
                username=f'nick_{uid}',
                email=f'user{uid}@example.com',
                bio=f'Hello, I am user {uid}',
                is_active=True
            ))
        for chunk in chunked(profile_objs, batch_size):
            UserProfile.objects.bulk_create(chunk, batch_size=batch_size)

        profile_ids = list(UserProfile.objects.values_list('user_id', flat=True))
        if not profile_ids:
            raise CommandError('No profiles available; check UserProfile creation')

        tag_count_before = Tag.objects.count()
        need_tags = max(0, n_tags - tag_count_before)
        tag_objs = [Tag(name=f'tag_{rand_word(8)}_{i}') for i in range(need_tags)]
        for chunk in chunked(tag_objs, batch_size):
            Tag.objects.bulk_create(chunk, batch_size=batch_size)
        tag_ids = list(Tag.objects.values_list('id', flat=True))
        if len(tag_ids) < n_tags:
            tag_ids = tag_ids[:n_tags]

        q_objs = []
        for i in range(n_questions):
            author_id = random.choice(profile_ids)
            q_objs.append(Question(
                author_id=author_id,
                name=f'Question {i}: {rand_word(10)}?',
                text=f'{rand_word(30)} {rand_word(30)} {rand_word(30)}',
                rating=random.randint(0, 50),
                is_active=True
            ))
        for chunk in chunked(q_objs, batch_size):
            Question.objects.bulk_create(chunk, batch_size=batch_size)
        question_ids = list(Question.objects.values_list('id', flat=True))

        qt_objs = []
        for qid in question_ids:
            k = random.randint(1, 3)
            chosen_tags = random.sample(tag_ids, min(k, len(tag_ids)))
            for tid in chosen_tags:
                qt_objs.append(QuestionTag(question_id=qid, tag_id=tid))
        for chunk in chunked(qt_objs, batch_size):
            QuestionTag.objects.bulk_create(chunk, batch_size=batch_size, ignore_conflicts=True)

        a_objs = []
        for i in range(n_answers):
            qid = random.choice(question_ids)
            author_id = random.choice(profile_ids)
            a_objs.append(Answer(
                question_id=qid,
                author_id=author_id,
                text=f'Answer {i}: {rand_word(50)}',
                rating=random.randint(0, 30),
                is_active=True
            ))
        for chunk in chunked(a_objs, batch_size):
            Answer.objects.bulk_create(chunk, batch_size=batch_size)
        answer_ids = list(Answer.objects.values_list('id', flat=True))

        by_question = defaultdict(list)
        for aid, qid in Answer.objects.values_list('id', 'question_id'):
            by_question[qid].append(aid)
        to_flip = 0
        update_ids = []
        for qid, aids in by_question.items():
            if aids and random.random() < 0.3:
                update_ids.append(random.choice(aids))
                to_flip += 1
        if update_ids:
            Answer.objects.filter(id__in=update_ids).update(is_correct=True)

        n_qvotes = n_votes // 2
        n_avotes = n_votes - n_qvotes

        def unique_pairs(left_ids, user_ids, target_count):
            pairs = set()
            L = len(left_ids)
            U = len(user_ids)
            if L == 0 or U == 0:
                return []
            attempts = 0
            max_attempts = target_count * 10
            while len(pairs) < target_count and attempts < max_attempts:
                lid = left_ids[random.randrange(L)]
                uid = user_ids[random.randrange(U)]
                pairs.add((lid, uid))
                attempts += 1
            return list(pairs)

        q_pairs = unique_pairs(question_ids, profile_ids, n_qvotes)
        a_pairs = unique_pairs(answer_ids, profile_ids, n_avotes)

        qvote_objs = []
        for qid, uid in q_pairs:
            is_liked = random.random() < 0.8
            val = 1 if is_liked else -1
            qvote_objs.append(QuestionLike(
                question_id=qid, user_id=uid,
                is_liked=is_liked, value=val
            ))
        for chunk in chunked(qvote_objs, batch_size):
            QuestionLike.objects.bulk_create(chunk, batch_size=batch_size, ignore_conflicts=True)

        avote_objs = []
        for aid, uid in a_pairs:
            is_liked = random.random() < 0.85
            val = 1 if is_liked else -1
            avote_objs.append(AnswerLike(
                answer_id=aid, user_id=uid,
                is_liked=is_liked, value=val
            ))
        for chunk in chunked(avote_objs, batch_size):
            AnswerLike.objects.bulk_create(chunk, batch_size=batch_size, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS('Done.'))
        self.stdout.write(self.style.SUCCESS(
            f'Created/ensured: users~{n_users}, profiles~{n_users}, '
            f'tags~{n_tags}, questions~{n_questions}, answers~{n_answers}, votes~{n_votes}'
        ))
