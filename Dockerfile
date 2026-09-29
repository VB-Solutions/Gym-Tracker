# API de Gym-Tracker (Django + gunicorn). Ver docs/DEPLOY.md para desplegarla en Coolify.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 1000 app

# Primero las dependencias: esta capa se reutiliza mientras no cambie requirements.txt
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=app:app . .

# collectstatic importa settings, que exige una SECRET_KEY: esta es solo para el build
RUN DJANGO_SECRET_KEY=build-only python manage.py collectstatic --noinput \
    && chown -R app:app /app/staticfiles

USER app

EXPOSE 8000

# Coolify usa este HEALTHCHECK. Python en vez de curl: la imagen slim no trae curl
HEALTHCHECK --interval=10s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/health/' % os.environ.get('PORT', '8000'), timeout=4)"

# Con `sh` no depende del permiso de ejecución (el repo se commitea desde Windows)
CMD ["sh", "/app/docker-entrypoint.sh"]
