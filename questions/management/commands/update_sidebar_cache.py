from datetime import timedelta

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Q, F, Value, IntegerField
from django.db.models.functions import Coalesce
from django.utils import timezone

from questions.models import Tag, QuestionTag

SIDEBAR_CACHE_KEY = "sidebar:v1"
CACHE_TTL_SECONDS = 600

User = get_user_model()


class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        tags_from = now - timedelta(days=90)
        users_from = now - timedelta(days=7)

        tag_rows = list(
            QuestionTag.objects.filter(question__is_active=True, question__created__gte=tags_from)
            .values("tag_id")
            .annotate(q_count=Count("question_id", distinct=True))
            .order_by("-q_count")[:10]
        )

        tag_ids = [r["tag_id"] for r in tag_rows]
        tags_map = Tag.objects.in_bulk(tag_ids)
        popular_tags = [tags_map[i] for i in tag_ids if i in tags_map]

        best_members = list(
            User.objects.filter(is_active=True)
            .select_related("profile")
            .annotate(
                q_score=Coalesce(
                    Sum(
                        "questions__rating",
                        filter=Q(questions__is_active=True, questions__created__gte=users_from),
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
                a_score=Coalesce(
                    Sum(
                        "answers__rating",
                        filter=Q(answers__is_active=True, answers__created__gte=users_from),
                    ),
                    Value(0),
                    output_field=IntegerField(),
                ),
            )
            .annotate(score=F("q_score") + F("a_score"))
            .order_by("-score", "-date_joined")[:10]
        )

        cache.set(
            SIDEBAR_CACHE_KEY,
            {"popular_tags": popular_tags, "best_members": best_members, "generated_at": now},
            CACHE_TTL_SECONDS,
        )

        self.stdout.write(f"ok tags={len(popular_tags)} users={len(best_members)}")
