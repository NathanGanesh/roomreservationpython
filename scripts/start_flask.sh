#!/bin/sh
set -eu

python - <<'PY'
import os
import sys
import time

import psycopg


def normalize_database_url(value: str) -> str:
    if value.startswith("postgresql+psycopg://"):
        return value.replace("postgresql+psycopg://", "postgresql://", 1)
    if value.startswith("postgres+psycopg://"):
        return value.replace("postgres+psycopg://", "postgres://", 1)
    return value


database_url = os.getenv("DATABASE_URL", "")

if not database_url or database_url.startswith("sqlite"):
    print("Skipping database wait because DATABASE_URL is not a PostgreSQL URL.", flush=True)
    sys.exit(0)

database_url = normalize_database_url(database_url)

for attempt in range(1, 31):
    try:
        with psycopg.connect(database_url, connect_timeout=2) as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        print("Database is ready.", flush=True)
        sys.exit(0)
    except Exception as exc:  # pragma: no cover - startup script
        print(f"Waiting for database ({attempt}/30): {exc}", flush=True)
        time.sleep(2)

print("Database did not become ready in time.", file=sys.stderr, flush=True)
sys.exit(1)
PY

echo "Applying database migrations..."
flask --app app:app db upgrade

echo "Starting Flask application..."
exec flask --app app:app run --host=0.0.0.0 --port=5000
