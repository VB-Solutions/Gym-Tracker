#!/bin/sh
# Arranque del contenedor de la API: migra la base, crea la tabla del cache y levanta gunicorn.
set -e

python manage.py migrate --noinput
# Tabla del cache compartido entre procesos (si ya existe, no hace nada)
python manage.py createcachetable

exec gunicorn django_crud_api_gym_tracker.wsgi:application \
    --bind "0.0.0.0:${PORT:-8000}" \
    --workers "${WEB_CONCURRENCY:-3}" \
    --access-logfile -
