from django.db import DatabaseError, connection
from django.http import HttpResponse


class HealthCheckMiddleware:
    """
    GET /health/ -> 200 "ok" si la app responde y llega a la base de datos, 503 si no.

    Va primera en MIDDLEWARE: el health check de Coolify (HEALTHCHECK del Dockerfile)
    corre dentro del contenedor contra http://127.0.0.1, así que no tiene que depender
    de ALLOWED_HOSTS ni de la redirección a HTTPS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path != '/health/':
            return self.get_response(request)

        try:
            connection.ensure_connection()
        except DatabaseError:
            return HttpResponse('database unavailable', status=503, content_type='text/plain')

        return HttpResponse('ok', content_type='text/plain')
