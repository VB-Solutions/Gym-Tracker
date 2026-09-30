# Deploy en Coolify

Gym-Tracker se despliega en Coolify como tres recursos del mismo proyecto:

| Recurso | Qué es | Cómo se construye |
|---|---|---|
| **PostgreSQL** | La base de datos | Base de datos administrada por Coolify |
| **API** | Django + gunicorn (puerto 8000) | `Dockerfile` de la raíz del repo |
| **Web** | React compilado, servido por nginx (puerto 80) | `client/Dockerfile` |

El proxy de Coolify (Traefik) pone el HTTPS delante de la API y de la web.

Las dos imágenes traen su propio `HEALTHCHECK`, y Coolify lo usa solo: no hace falta configurar el health check en el panel.

- **API:** `GET /health/`, que devuelve 200 si la app responde y llega a la base, o 503 si no.
- **Web:** `GET /`.

## 1. PostgreSQL

1. En el proyecto: **+ New → Databases → PostgreSQL**, en el mismo servidor donde van a correr la API y la web.
2. Iniciarla (**Start**).
3. Copiar **Postgres URL (internal)**. Tiene la forma `postgres://postgres:<clave>@<id-del-contenedor>:5432/postgres` y es el `DATABASE_URL` de la API.

## 2. API (Django)

1. **+ New → Private Repository (with GitHub App)** si el repo es privado, o **Public Repository** si no.
   - Repositorio: `VB-Solutions/Gym-Tracker`.
   - Branch: `coolify-test`.
2. Configuración general:
   - **Build Pack:** `Dockerfile`.
   - **Base Directory:** `/`.
   - **Dockerfile Location:** `/Dockerfile`.
   - **Ports Exposes:** `8000`.
   - **Domains:** por ejemplo `https://api.tu-dominio.com`, con `https://` incluido. Si no hay dominio propio, se puede usar el dominio `sslip.io` que genera Coolify.
3. **Environment Variables.** En todas, **desmarcar "Build Variable"**: la API solo las usa en runtime, y así los secretos no quedan en la imagen.

   | Variable | Valor |
   |---|---|
   | `DJANGO_SECRET_KEY` | Generar una: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
   | `DJANGO_DEBUG` | `False` |
   | `DJANGO_ALLOWED_HOSTS` | `api.tu-dominio.com` (sin `https://`) |
   | `DJANGO_CSRF_TRUSTED_ORIGINS` | `https://api.tu-dominio.com` (para iniciar sesión en `/admin/`) |
   | `DJANGO_CORS_ORIGINS` | La URL de la web, ej. `https://app.tu-dominio.com` (se completa en el paso 4) |
   | `DJANGO_BEHIND_PROXY` | `True` (Traefik termina el HTTPS y avisa con `X-Forwarded-Proto`) |
   | `DATABASE_URL` | La URL interna del paso 1 |
   | `WEB_CONCURRENCY` | Opcional: procesos de gunicorn (por defecto 3) |

4. **Deploy.** Al arrancar, el contenedor aplica las migraciones (`migrate`) y levanta gunicorn. En **Logs** se ven las migraciones y cada pedido.

## 3. Superusuario

En la API, pestaña **Terminal**, ejecutar:

```sh
python manage.py createsuperuser
```

Con ese usuario, en `https://api.tu-dominio.com/admin/`:

1. Crear el primer gimnasio.
2. Darle a alguien una membresía ADMIN en ese gimnasio.

Desde ahí, el resto se hace por la API (ver [README](../README.md#gimnasios-usuarios-y-roles)).

## 4. Web (React)

1. **+ New**, mismo repositorio y branch (`coolify-test`).
2. Configuración general:
   - **Build Pack:** `Dockerfile`.
   - **Base Directory:** `/client`.
   - **Dockerfile Location:** `/Dockerfile`, relativo a la base directory.
   - **Ports Exposes:** `80`.
   - **Domains:** por ejemplo `https://app.tu-dominio.com`.
3. **Environment Variables:**

   | Variable | Valor | Tipo |
   |---|---|---|
   | `VITE_API_URL` | `https://api.tu-dominio.com` | **Build Variable** (Vite la incrusta en el build) |

4. **Deploy.**
5. En la API, poner la URL de la web en `DJANGO_CORS_ORIGINS` y **redeployar la API**. Los cambios de variables se aplican recién al reiniciar el contenedor.

Cambiar `VITE_API_URL` requiere un nuevo deploy de la web, porque el valor queda compilado en el JavaScript.

> Por ahora el frontend no llama a la API; ver P0 en el [roadmap](ROADMAP.md). `VITE_API_URL` queda lista para cuando se agregue esa capa.

## 5. Verificar

| URL | Esperado |
|---|---|
| `https://api.tu-dominio.com/health/` | `ok` |
| `https://api.tu-dominio.com/gym_tracker/docs/` | Swagger. El botón **Authorize** acepta el token de `/users/auth/login/` |
| `https://api.tu-dominio.com/admin/` | Admin de Django con estilos (los sirve whitenoise) |
| `http://api.tu-dominio.com/...` | Redirige a `https://` |
| `https://app.tu-dominio.com/login` | La pantalla de login. Las rutas del SPA las resuelve nginx con `index.html` |

## Problemas comunes

| Síntoma | Causa probable |
|---|---|
| La API queda **unhealthy** o no arranca | `DATABASE_URL` mal copiada, o la base no está iniciada o está en otro servidor. Revisar los **Logs**: si `migrate` falla, el contenedor no llega a levantar gunicorn |
| `400 Bad Request` en todas las URLs de la API | El dominio no está en `DJANGO_ALLOWED_HOSTS` |
| Redirección infinita a HTTPS | Falta `DJANGO_BEHIND_PROXY=True` |
| "CSRF verification failed" al iniciar sesión en el admin | Falta el dominio con `https://` en `DJANGO_CSRF_TRUSTED_ORIGINS` |
| El navegador bloquea los pedidos de la web a la API (CORS) | La URL de la web no está en `DJANGO_CORS_ORIGINS`, o la API no se redeployó después de cambiarla |

## Notas

- **HSTS:** con `DJANGO_DEBUG=False` la API manda HSTS por 30 días (`DJANGO_HSTS_SECONDS`). Los navegadores recuerdan que el dominio es solo HTTPS, así que conviene tener el certificado funcionando antes de apuntar el dominio definitivo.
- **Throttling de login y registro:** el límite (20 por minuto) se cuenta en una tabla de PostgreSQL (`django_cache`), compartida por todos los procesos de gunicorn. El contenedor la crea al arrancar con `createcachetable`.
- **Backups:** se configuran en el recurso de PostgreSQL (**Backups**) de Coolify.

## Probar las imágenes en local

Con Docker:

```sh
docker network create gym-net
docker run -d --name gym-db --network gym-net -e POSTGRES_USER=gym -e POSTGRES_PASSWORD=gym -e POSTGRES_DB=gym postgres:17-alpine

docker build -t gym-api .
docker run -d --name gym-api --network gym-net -p 8000:8000 \
  -e DATABASE_URL=postgres://gym:gym@gym-db:5432/gym \
  -e DJANGO_SECRET_KEY=solo-para-probar -e DJANGO_DEBUG=False \
  -e DJANGO_ALLOWED_HOSTS=localhost -e DJANGO_BEHIND_PROXY=True \
  gym-api

docker build -t gym-web --build-arg VITE_API_URL=http://localhost:8000 client
docker run -d --name gym-web -p 8080:80 gym-web
```

Sin un proxy con HTTPS delante, la API redirige a `https://`. Para probarla directo, mandar el header `X-Forwarded-Proto: https`:

```sh
curl -H "X-Forwarded-Proto: https" http://localhost:8000/gym_tracker/docs/
```

Los tests también se pueden correr contra PostgreSQL dentro de la imagen:

```sh
docker run --rm --network gym-net -e DATABASE_URL=postgres://gym:gym@gym-db:5432/gym \
  -e DJANGO_SECRET_KEY=test -e DJANGO_DEBUG=True gym-api python manage.py test
```
