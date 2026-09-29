# Gym-Tracker

App para gimnasios: cada gimnasio tiene ejercicios estándar (globales) y propios, videos explicativos, y rutinas que los entrenadores arman para sus socios.

Cada usuario tiene un rol en cada gimnasio al que pertenece:

- **ADMIN**: administra el gimnasio, gestiona sus miembros y ve todas sus rutinas.
- **STAFF**: entrenador. Crea ejercicios propios, videos y rutinas.
- **PERSON**: socio. Ve sus rutinas.

El estado actual del proyecto y lo que falta está en [docs/ROADMAP.md](docs/ROADMAP.md).

## Stack

| Parte | Tecnologías |
|---|---|
| Backend | Python 3.13, Django 6, Django REST Framework, SimpleJWT, drf-spectacular (Swagger), SQLite |
| Frontend (`client/`) | React 19, TypeScript, Vite 8, Tailwind 4, shadcn/ui, motion |

```
django_crud_api_gym_tracker/   configuración del proyecto Django (settings, urls)
gym_tracker/                   gimnasios, músculos, ejercicios, videos, rutinas y sus bloques
users/                         usuarios (login por email), membresías con rol por gimnasio y auth JWT
client/                        frontend React
```

## Backend

Requiere Python 3.12 o superior (Django 6).

1. Crear el entorno virtual e instalar las dependencias:

   ```powershell
   py -3.13 -m venv .venv
   .\.venv\Scripts\Activate.ps1        # en bash: source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Crear la configuración local copiando `.env.example` a `.env` y completando `DJANGO_SECRET_KEY`. Para generar una clave:

   ```powershell
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

3. Crear la base de datos y un superusuario:

   ```powershell
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Levantar el servidor:

   ```powershell
   python manage.py runserver
   ```

La API queda en `http://127.0.0.1:8000`:

- Swagger: `/gym_tracker/docs/`
- Admin de Django: `/admin/`

### Gimnasios, usuarios y roles

El rol de un usuario es **por gimnasio**: alguien puede ser STAFF en un gimnasio y socio en otro. El dato vive en `GymMembership` (usuario, gimnasio, rol).

Para arrancar desde cero:

1. En `/admin/`, con el superusuario, crear un gimnasio.
2. Crear o elegir un usuario y agregarle una membresía ADMIN en ese gimnasio (sección "Gym memberships" del usuario).
3. Desde ahí, ese ADMIN maneja su gimnasio por la API:
   - la gente se registra en `POST /users/auth/register/`;
   - el ADMIN la suma con `POST /users/memberships/`, pasando `{gym, email, role}`.

### Autenticación

La API usa JWT:

1. `POST /users/auth/login/` con `{"email", "password"}` devuelve `{"access", "refresh"}`.
2. Cada pedido lleva el header `Authorization: Bearer <access>`.
3. El access vence a los 30 minutos. Para pedir uno nuevo: `POST /users/auth/refresh/` con `{"refresh"}`. El refresh dura 7 días.

Ejemplo en PowerShell:

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/users/auth/login/ `
  -ContentType 'application/json' -Body '{"email": "staff@test.com", "password": "..."}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/users/me/ -Headers @{ Authorization = "Bearer $($login.access)" }
```

En Swagger se puede pegar el token con el botón **Authorize**. Otra opción: iniciar sesión en `/admin/` y usar la API navegable en el mismo navegador.

Los endpoints y los permisos por rol están en [docs/ROADMAP.md](docs/ROADMAP.md#estado-actual). Todos los listados vienen paginados: `{count, next, previous, results}`.

### Tests

```powershell
python manage.py test
```

En GitHub Actions (`.github/workflows/backend.yml`) corren en cada push a `main` y en cada PR:

- el system check;
- el chequeo de migraciones pendientes;
- la validación del schema OpenAPI;
- los tests.

### Producción

La API y la web se despliegan en **Coolify**, con PostgreSQL. El paso a paso está en [docs/DEPLOY.md](docs/DEPLOY.md).

- **Imágenes:** una para la API (`Dockerfile`, gunicorn con whitenoise para los estáticos) y otra para la web (`client/Dockerfile`, nginx).
- **Arranque:** el contenedor de la API aplica las migraciones al iniciar.
- **Modo producción:** con `DJANGO_DEBUG=False` se activan las cookies seguras, la redirección a HTTPS y HSTS.
- **Variables:** están documentadas en `.env.example`.

## Frontend

Requiere Node 20.19+ o 22.12+.

```powershell
cd client
npm install
npm run dev        # http://localhost:5173
```

Otros scripts: `npm run build`, `npm run lint`, `npm run preview`.

El backend acepta pedidos del frontend por CORS desde los orígenes de `DJANGO_CORS_ORIGINS` (por defecto `http://localhost:5173`).
