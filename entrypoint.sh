#!/usr/bin/env bash
set -e

python - <<'PY'
import os, time, sys
import psycopg
url = os.getenv("DATABASE_URL")
for i in range(60):
    try:
        with psycopg.connect(url, connect_timeout=3) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
        print("db ok")
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
PY

python manage.py migrate --noinput

if [ -z "${FILL_RATIO}" ]; then
  RATIO=100
else
  RATIO="${FILL_RATIO}"
fi

if [ ! -f /app/.bootstrapped ]; then
  python manage.py fill_db "${RATIO}" || true
  touch /app/.bootstrapped
fi

python manage.py runserver 0.0.0.0:8000
