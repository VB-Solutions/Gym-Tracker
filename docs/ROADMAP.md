# Estado actual y roadmap

Última revisión: 29/09/2026, después de preparar el deploy en Coolify (rama `coolify-test`).

## Resumen

- **El backend está completo para un primer uso real.**
  - Registro y login con JWT.
  - Roles por gimnasio, y un ADMIN que gestiona a los miembros de su gimnasio.
  - Ejercicios estándar y propios, videos, y rutinas con sus bloques de ejercicios.
  - Tests y CI en GitHub Actions.
- **El frontend sigue siendo solo pantallas estáticas.** Conectarlo a la API es lo principal que falta (P0).
- **El deploy está listo para Coolify** ([docs/DEPLOY.md](DEPLOY.md)):
  - API con gunicorn y PostgreSQL.
  - Web con nginx.
  - Health checks en las dos imágenes.
  - Tests en CI contra PostgreSQL.

## Estado actual

### Roles

El rol es **por gimnasio** (`users.GymMembership`): un usuario puede ser STAFF en un gimnasio y socio en otro. Si deja un gimnasio, deja de ver lo de ese gimnasio.

| Rol | Puede |
|---|---|
| ADMIN | Todo lo de STAFF, más: ver todas las rutinas del gym, asignarle una rutina a cualquier entrenador y gestionar los miembros |
| STAFF | Crear ejercicios propios, videos y rutinas; editar las rutinas que armó y sus bloques |
| PERSON | Ver sus rutinas con sus bloques y renombrarlas |

### Endpoints

Todos los endpoints requieren un token JWT (`Authorization: Bearer <access>`), salvo login, refresh, registro, el schema y Swagger.

- **Paginación:** los listados vienen paginados (`{count, next, previous, results}`, 20 por página, `?page_size` hasta 100).
- **`?gym=<id>`:** tiene que ser un número (si no, 400) y un gimnasio al que pertenezcas (si no, 403).

**Autenticación (`/users/`)**

| Endpoint | Qué hace |
|---|---|
| `POST auth/register/` | Alta pública con email, contraseña, nombre y apellido. El usuario queda sin gimnasios |
| `POST auth/login/`, `POST auth/refresh/` | Tokens JWT: el access dura 30 minutos y el refresh 7 días. Máximo 20 pedidos por minuto |
| `GET/PATCH me/` | El usuario logueado, con sus gimnasios y su rol en cada uno. Se puede editar el nombre |

**Usuarios y miembros (`/users/`)**

| Endpoint | Lectura | Escritura |
|---|---|---|
| `memberships/` | ADMIN: las membresías de sus gimnasios | ADMIN: sumar por email, cambiar el rol, sacar. El gym siempre queda con al menos un ADMIN |
| `admins/`, `staff/` | Usuarios con ese rol en tus gimnasios | — |
| `people/` | Solo STAFF o ADMIN: socios de los gimnasios donde tienen ese rol | — |

**Gimnasios y ejercicios (`/gym_tracker/`)**

| Endpoint | Lectura | Escritura |
|---|---|---|
| `gyms/` | Tus gimnasios | Desde el admin de Django |
| `muscles/` | Todos | Desde el admin de Django |
| `exercises/` | Los estándar; con `?gym` suma los propios de ese gym | Desde el admin de Django |
| `custom-exercises/` | Listar exige `?gym` | STAFF o ADMIN del gym. El nombre es único por gym. No se puede borrar si está en una rutina |
| `gym-standard-exercise-videos/` | Listar exige `?gym` | STAFF o ADMIN del gym. Un video por ejercicio estándar y gym |

**Rutinas (`/gym_tracker/`)**

| Endpoint | Lectura | Escritura |
|---|---|---|
| `routines/` | Las que podés ver según tu rol; `?gym` opcional. Incluye los bloques con el video que corresponde a ese gym | Crear y borrar: STAFF o ADMIN. Editar: solo el nombre |
| `exercise-blocks/` | Listar exige `?routine` | STAFF o ADMIN del gym de la rutina |

Además, públicos:

- `/gym_tracker/api/schema/`: el schema OpenAPI.
- `/gym_tracker/docs/`: Swagger, donde el token se carga con el botón **Authorize**.

### Modelo de datos

- **`Gym`**: gimnasio. El nombre es único sin importar mayúsculas.
- **`Muscle`**: músculo, con su zona. El nombre es único sin importar mayúsculas.
- **`Exercise`**: ejercicio estándar global. Si se borra el músculo, el ejercicio queda sin músculo.
- **`CustomExercise`**: ejercicio propio de un gym. Hereda de `Exercise`, el gym es obligatorio y puede tener video.
- **`GymStandardExerciseVideo`**: el video que un gym le pone a un ejercicio estándar.
- **`Routine`**: rutina de un gym, armada por un STAFF o ADMIN para un PERSON de ese gym.
- **`ExerciseBlock`**: un ejercicio dentro de una rutina.
  - Tiene día, orden y `series_data`, con formato `[{"repe": 12, "peso": 50}, ...]`.
  - Día y orden empiezan en 1, y la combinación rutina, día y orden es única.
  - Un ejercicio que está en una rutina no se puede borrar.
- **`users.User`**: login por email. Su relación con `Gym` pasa por **`GymMembership`** (usuario, gimnasio, rol), única por usuario y gimnasio.

### Calidad

- **70 tests** en `gym_tracker/tests.py`, `users/tests.py` y `django_crud_api_gym_tracker/tests.py`. Pasan con SQLite y con PostgreSQL. Cubren:
  - permisos por rol y por gimnasio;
  - el flujo JWT y el throttling;
  - la gestión de miembros;
  - las validaciones;
  - que la cantidad de queries de las rutinas no crezca;
  - las migraciones con datos (`users.0002` y `gym_tracker.0010`);
  - el admin de usuarios.
- **CI en GitHub Actions:**
  - `backend.yml`: system check, migraciones pendientes, schema OpenAPI y tests contra PostgreSQL.
  - `docker.yml`: build de las dos imágenes.
- **Producción:** `check --deploy` solo marca W005 y W021 (HSTS para subdominios y preload). Quedan apagados a propósito hasta conocer el dominio.

### Frontend

- **Rutas:**
  - `/` y `/login` muestran Login.
  - `/register` muestra Register.
  - `/home` muestra 5 tarjetas de ejemplo.
  - `*` muestra la página de error.
- **Sin conexión a la API.** No hay cliente HTTP, los handlers de login y registro están vacíos y `/home` es pública.
- `npm run build` funciona. `npm run lint` marca 7 problemas: 5 errores y 2 warnings (detalle en P2).

## Trabajo futuro

### P0: conectar el frontend

1. **Capa de API en `client/`.**
   - `axios` con la base URL en `VITE_API_URL`.
   - Guardar los tokens de `/users/auth/login/` y refrescarlos con `/users/auth/refresh/` cuando el access vence (401).
   - `axios`, `react-hook-form` y `react-hot-toast` estaban en el `package.json` suelto que se borró de la raíz; hay que instalarlos en `client/`.
2. **Auth en la UI.**
   - Contexto de auth con `/users/me/`, rutas protegidas y logout.
   - Conectar Login y Register. Al Register le faltan los campos de nombre y apellido.
3. **Pantallas según el rol en cada gym**, que está en `me.gyms[].role`:
   - PERSON: sus rutinas.
   - STAFF: ejercicios, videos, y rutinas con sus bloques.
   - ADMIN: además, gestión de miembros.
   - Los listados vienen paginados.

### P1: despliegue y backend pendiente

**Despliegue**
- **Hacer el primer deploy en Coolify** siguiendo [DEPLOY.md](DEPLOY.md), y configurar los backups de PostgreSQL.
- **Decidir HSTS** (`SECURE_HSTS_INCLUDE_SUBDOMAINS` y `SECURE_HSTS_PRELOAD`) cuando esté el dominio definitivo.
- **Cache compartido.** El throttling de login y registro se guarda en la memoria de cada proceso de gunicorn, así que el límite real se multiplica por la cantidad de procesos. Pasar a un cache compartido: Redis como recurso de Coolify, o el cache en base de datos de Django.

**Auth y cuentas**
- **Logout real.** Hoy el cliente descarta los tokens, pero el refresh sigue valiendo hasta que vence. Se resuelve con la app `token_blacklist` de SimpleJWT.
- **Recuperar contraseña por email.** Hace falta configurar el envío de emails.
- **Email sin distinguir mayúsculas.** El registro ya rechaza emails repetidos sin importar mayúsculas, pero el login compara exacto. Guardar el email en minúsculas o hacer que el login no distinga mayúsculas.

**Datos**
- **Alta de gimnasios.** Hoy solo el superusuario los crea desde el admin. Si hace falta que un dueño de gimnasio se dé de alta solo, agregar un endpoint que cree el gym y la membresía ADMIN.
- **Nombres de ejercicios estándar.** No tienen restricción de unicidad: los carga el superusuario desde el admin, y la herencia de `CustomExercise` impide una constraint en la base.

### P2: mejoras

**Producto**
- **Registro de entrenamientos.** Hoy `series_data` es lo que el entrenador indica. Si el socio va a anotar lo que hizo (repeticiones y peso reales, por fecha), conviene un modelo aparte en vez de editar la rutina.
- **Throttling general de la API.** Hoy solo están limitados login, refresh y registro.

**Frontend: estructura**
- Crear una ruta de layout con `<Outlet/>`. Hoy cada vista repite Navbar y Footer.
- Generar las tarjetas de Home desde datos en vez de copiarlas 5 veces.
- La página de error no tiene link para volver.

**Frontend: formularios y navegación**
- **El botón "Continuar" está fuera del `<form>`** (`Login.tsx:46`, `Register.tsx:52`). Por eso `required` no se valida y Enter no envía.
- **Labels que no apuntan a su input.**
  - En Login, los inputs no tienen `id`.
  - En Register, las dos labels de contraseña usan `htmlFor="password"` (`Register.tsx:38` y `:43`).
- **La navbar trata `/` como home** (`navbar.tsx:15`), pero `/` muestra Login.

**Frontend: accesibilidad**
- Usar `lang="es"` en `index.html:2`.
- Mejorar el contraste del violeta y el amarillo.
- Respetar `prefers-reduced-motion` en las animaciones.

**Lint del frontend (7 problemas)**
- `react-hooks/set-state-in-effect`: `navbar.tsx:21` y `motion-primitives/magnetic.tsx:81`.
- `react-hooks/exhaustive-deps`: `navbar.tsx:26` y `magnetic.tsx:64`.
- `@typescript-eslint/no-unused-vars`: `motion-primitives/text-effect.tsx:183`.
- `react-refresh/only-export-components`: `ui/button.tsx:67` y `ui/button-group.tsx:82`.

**Limpieza del cliente**
- Dependencias sin usar: `lucide-react` y `vite-plugin-svgr`.
- Componentes sin usar: `tilt.tsx` y `button-group.tsx`.
- `components.json:7` apunta a `tailwind.config.js`, que ya no existe.
- **CI del frontend:** `npm run lint` y `npm run build`, en un workflow aparte del backend.

## Hecho

**Rama `fix/critical-and-cleanup`**
- Errores 500 en las escrituras por permisos mal combinados.
- `/users/` ya no es público.
- `?gym` inválido devuelve 400.
- CORS configurado.
- Limpieza del repo y settings por variables de entorno.

**Rama `feat/backend-roadmap`**
- **Roles y auth:** roles por gimnasio, auth JWT, gestión de miembros y admin de usuarios.
- **API:**
  - API de bloques de rutina con validación de `series_data`.
  - `video_url` corregido, sin N+1 en las rutinas, y paginación.
  - Validación de videos.
  - Permisos de rutinas: acceso solo mientras se pertenece al gym, y renombrar una rutina después de que el socio se fue.
  - Se eliminó el endpoint duplicado `/routines/all/`.
- **Datos:** `on_delete` corregidos, gym obligatorio en ejercicios propios y nombres únicos.
- **Mantenimiento:**
  - Squash de las migraciones de tutorial.
  - Mensajes en español.
  - Settings de producción.
  - CI.

**Rama `coolify-test`**
- **Imágenes Docker:**
  - API: gunicorn, whitenoise, migraciones al arrancar y `HEALTHCHECK` en `/health/`.
  - Web: nginx con fallback de SPA.
- **PostgreSQL** por `DATABASE_URL`, con SQLite en desarrollo.
- **Logs de errores** a la consola.
- **CI** con PostgreSQL y build de las dos imágenes.
- **Guía de deploy** en Coolify.
