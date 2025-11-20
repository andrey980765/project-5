#!/usr/bin/env bash
set -e

# wait-for-postgres
if [ -n "$DATABASE_URL" ] || [ -n "$POSTGRES_DB" ]; then
  echo "Waiting for postgres..."
  MAX_RETRIES=20
  attempt=0
  until python - <<PY
import sys, time
from urllib.parse import urlparse
import os
import psycopg2
try:
    user=os.environ.get('POSTGRES_USER')
    pw=os.environ.get('POSTGRES_PASSWORD')
    db=os.environ.get('POSTGRES_DB')
    host=os.environ.get('POSTGRES_HOST','db')
    port=os.environ.get('POSTGRES_PORT',5432)
    conn = psycopg2.connect(dbname=db, user=user, password=pw, host=host, port=port)
    conn.close()
    print("postgres ok")
except Exception as e:
    print("wait", e)
    sys.exit(1)
PY
  do
    attempt=$((attempt+1))
    if [ $attempt -gt $MAX_RETRIES ]; then
      echo "Postgres did not become ready in time"
      exit 1
    fi
    sleep 2
  done
fi

# Выполнить миграции
echo "Apply database migrations..."
python manage.py migrate --noinput

# Собрать статические файлы
echo "Collect static..."
python manage.py collectstatic --noinput

# Создать/обновить суперпользователя? (опционально)
# python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

exec "$@"
