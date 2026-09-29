#!/bin/sh
# Arranque del contenedor de la API: migra la base y levanta gunicorn.
set -e

python manage.py migrate --noinput

exec gunicorn django_crud_api_gym_tracker.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --access-logfile -
