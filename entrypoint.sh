#!/bin/bash
set -e

while ! nc -z "$DB_HOST" "$DB_PORT"; do
  sleep 1
done

mkdir -p /app/media /app/static /app/frontend/build/static

if [ "$SERVICE_NAME" = "web" ]; then
    python manage.py migrate
    if [ "${COLLECTSTATIC:-0}" = "1" ]; then
        python manage.py collectstatic --noinput
    fi
    if [ "${START_FRONTEND_DEV_SERVER:-0}" = "1" ]; then
        cd /app/frontend
        if [ ! -x /app/frontend/node_modules/.bin/vite ]; then
            echo "Missing frontend dependencies in /app/frontend/node_modules. Rebuild the image or install them before starting web." >&2
            exit 1
        fi
        npm start &
        cd /app
    fi
    exec python manage.py runserver 0.0.0.0:8000
fi

if [ "$SERVICE_NAME" = "celery_worker" ]; then
    exec celery -A pampApp worker -l info
fi

if [ "$SERVICE_NAME" = "celery_beat" ]; then
    exec celery -A pampApp beat -l info
fi

echo "Unknown SERVICE_NAME: $SERVICE_NAME" >&2
exit 1
