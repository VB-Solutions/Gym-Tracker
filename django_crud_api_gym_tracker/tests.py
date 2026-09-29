from unittest import mock

from django.db import OperationalError, connection
from django.test import TestCase, override_settings


class HealthCheckTests(TestCase):
    def test_returns_ok(self):
        response = self.client.get('/health/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')

    @override_settings(ALLOWED_HOSTS=['api.example.com'], SECURE_SSL_REDIRECT=True)
    def test_ignores_allowed_hosts_and_https_redirect(self):
        # Así lo llama el HEALTHCHECK del Dockerfile: http://127.0.0.1:8000/health/
        response = self.client.get('/health/', HTTP_HOST='127.0.0.1')
        self.assertEqual(response.status_code, 200)

        # El resto del sitio sigue validando el host
        response = self.client.get('/gym_tracker/muscles/', HTTP_HOST='127.0.0.1')
        self.assertEqual(response.status_code, 400)

    def test_reports_database_errors(self):
        with mock.patch.object(connection, 'ensure_connection', side_effect=OperationalError):
            response = self.client.get('/health/')

        self.assertEqual(response.status_code, 503)
