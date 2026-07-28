#!/usr/bin/env sh
set -eu

cd /app/backend

if [ -z "${DATABASE_URL:-}" ] && [ -n "${POSTGRES_PASSWORD:-}" ]; then
  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@${POSTGRES_HOST:-db}:${POSTGRES_PORT:-5432}/${POSTGRES_DB:-promocode_checker}"
fi

if [ -z "${DATABASE_URL:-}" ]; then
  echo "DATABASE_URL is required (or POSTGRES_* variables)." >&2
  python /app/scripts/notify_startup_failure.py "DATABASE_URL missing on container start" || true
  exit 1
fi

echo "Running database migrations..."
if ! python -m alembic upgrade head; then
  echo "Migration failed." >&2
  python /app/scripts/notify_startup_failure.py "Alembic migration failed on container start" || true
  exit 1
fi

if [ "${AUTO_SEED_PROMOCODES:-}" = "1" ] || [ "${AUTO_SEED_PROMOCODES:-}" = "true" ]; then
  echo "Seeding demo promocodes..."
  python /app/scripts/seed_promocodes.py || true
fi

port="${PORT:-${APP_PORT:-8000}}"
echo "Starting uvicorn on 0.0.0.0:${port}..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "${port}" --app-dir /app/backend
