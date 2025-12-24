from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("questions", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS question_fts_gin
            ON "Question"
            USING GIN (to_tsvector('russian', coalesce(name,'') || ' ' || coalesce(text,'')));
            """,
            reverse_sql="""
            DROP INDEX IF EXISTS question_fts_gin;
            """,
        ),
    ]
