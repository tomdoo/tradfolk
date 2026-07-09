#!/usr/bin/env sh
set -e

echo "Waiting for db..."
python - <<'PY'
import os, time, psycopg2
for _ in range(60):
    try:
        psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST", "db"),
            port=os.getenv("POSTGRES_PORT", "5432")
        ).close()
        print("DB ready")
        break
    except Exception:
        time.sleep(1)
else:
    raise RuntimeError("DB not ready")
PY

alembic upgrade head
python -m app.import_proposals

APP_ENV="${APP_ENV:-prod}"

if [ "$APP_ENV" = "dev" ]; then
    echo "Starting backend in dev mode (gunicorn --reload, debug logs)..."
    exec gunicorn --reload --log-level debug -w 1 -b 0.0.0.0:8000 app.main:app
fi

echo "Starting backend in prod mode..."
exec gunicorn -w "${GUNICORN_WORKERS:-2}" --log-level "${GUNICORN_LOG_LEVEL:-info}" -b 0.0.0.0:8000 app.main:app
