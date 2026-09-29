# Estado actual y roadmap

Última revisión: 29/09/2026, después de corregir los bugs críticos y limpiar el repo (rama `fix/critical-and-cleanup`).

## Resumen

- **El backend es un prototipo que funciona por API.** Se pueden leer y escribir gimnasios, ejercicios, videos y rutinas, con permisos por rol y por gimnasio. Pero no hay endpoint de login, así que solo se puede usar con Basic Auth o con la sesión del admin.
- **El frontend son pantallas estáticas.** Login, Register y Home existen, pero no llaman a la API.
- **Lo que falta para que la app funcione de punta a punta** es la prioridad P0 de este documento: auth por API, la capa de API en el cliente y la gestión de usuarios y bloques de rutina.

## Estado actual

### Backend: endpoints y permisos

Todos los endpoints requieren estar autenticado, salvo el schema y Swagger. `?gym=<id>` tiene que ser un número y un gimnasio al que pertenezcas; si no, la respuesta es 400 o 403.

| Endpoint | Lectura | Escritura |
|---|---|---|
| `/gym_tracker/gyms/` | Tus gimnasios | — |
| `/gym_tracker/muscles/` | Todos | — |
| `/gym_tracker/exercises/` | Estándar; con `?gym` suma los propios de ese gym | — |
| `/gym_tracker/custom-exercises/` | Listar exige `?gym` | STAFF o ADMIN, en su gym |
| `/gym_tracker/gym-standard-exercise-videos/` | Listar exige `?gym` | STAFF o ADMIN, en su gym |
| `/gym_tracker/routines/` | Listar exige `?gym`. PERSON ve las suyas, STAFF las que creó, ADMIN todas las del gym | Crear y borrar: STAFF o ADMIN. Editar: cualquiera dentro de su alcance; el PERSON solo la suya, y no puede cambiar el `staff` |
| `/gym_tracker/routines/all/` | Igual que el listado, con `?gym` opcional | — |
| `/users/admins/`, `/users/staff/` | Usuarios que comparten gimnasio con vos | — |
| `/users/people/` | Solo STAFF o ADMIN; socios que comparten gimnasio | — |
| `/gym_tracker/api/schema/`, `/gym_tracker/docs/` | Público | — |

### Backend: modelo de datos

- **`Gym`**: gimnasio.
- **`Muscle`**: músculo, con su zona.
- **`Exercise`**: ejercicio estándar global, ligado a un músculo.
- **`CustomExercise`**: hereda de `Exercise` y pertenece a un gym. Puede tener video.
- **`GymStandardExerciseVideo`**: el video que un gym le pone a un ejercicio estándar. Es único por gym y ejercicio.
- **`Routine`**: rutina de un gym, armada por un STAFF para un PERSON.
- **`ExerciseBlock`**: un ejercicio dentro de una rutina, con día, orden y `series_data` (JSON). La combinación rutina, día y orden es única.
- **`users.User`**: login por email, un `role` global (ADMIN, STAFF o PERSON) y una relación M2M con `Gym`.

### Backend: calidad

- 14 tests de API en `gym_tracker/tests.py` y `users/tests.py`. Cubren permisos, el parámetro `?gym` y la generación del schema.
- `manage.py check` no reporta problemas, no hay migraciones pendientes y el schema OpenAPI valida sin warnings.
- La autenticación es la que DRF trae por defecto: sesión y Basic. No hay endpoints de login, registro ni token.

### Frontend

- **Rutas:**
  - `/` y `/login` muestran Login.
  - `/register` muestra Register.
  - `/home` muestra 5 tarjetas de ejemplo.
  - `*` muestra la página de error.
- **Sin conexión a la API.**
  - Los handlers de login y registro están vacíos.
  - No hay cliente HTTP.
  - No hay contexto de autenticación.
  - `/home` es pública.
- `npm run build` funciona. `npm run lint` marca 7 problemas: 5 errores y 2 warnings (detalle en P2).

## Trabajo futuro

### P0: que la app funcione de punta a punta

1. **Auth por API.**
   - Agregar `djangorestframework-simplejwt` con login y refresh.
   - Crear un endpoint de registro con email, contraseña, nombre y apellido. El rol por defecto es PERSON.
   - Crear un endpoint `me`.
   - En `REST_FRAMEWORK`, definir `DEFAULT_AUTHENTICATION_CLASSES` y `DEFAULT_PERMISSION_CLASSES = [IsAuthenticated]`, para que un endpoint nuevo no quede público por olvido.
2. **Capa de API en el cliente.**
   - Agregar `axios` con la base URL en `VITE_API_URL`.
   - Guardar el token y refrescarlo.
   - Crear un contexto de auth, rutas protegidas y logout.
   - Conectar los formularios de Login y Register. Faltan campos: el `User` tiene `first_name` y `last_name`, y Register solo pide email y contraseña.
   - `axios`, `react-hook-form` y `react-hot-toast` estaban en un `package.json` suelto en la raíz; hay que instalarlos en `client/`.
3. **Gestión de usuarios y membresías.**
   - `users/admin.py` está vacío: registrar `User` en el admin.
   - Crear endpoints para que un ADMIN sume STAFF y socios a su gimnasio. Hoy solo se puede desde el shell.
4. **API de `ExerciseBlock`.** Está comentada en `gym_tracker/views.py:292`. Sin ella las rutinas creadas por API quedan vacías; los bloques solo se cargan desde el admin.
5. **Pantallas del frontend** para gimnasios, ejercicios y rutinas, según el rol.

### P1: correcciones de modelo y API

**Modelo de datos**
- **El rol es global.** Un usuario no puede ser STAFF en un gym y socio en otro. Reemplazar `role` más la M2M por un modelo de membresía (`user`, `gym`, `role`).
- **`on_delete` demasiado agresivo.**
  - Borrar un `Muscle` borra sus ejercicios. Debería ser `SET_NULL`; el campo ya es nullable.
  - Borrar un `Exercise` borra bloques de rutinas de socios. Debería ser `PROTECT`.
- **`CustomExercise.gym` es nullable.** Un ejercicio propio sin gym no aparece en ningún endpoint.
- Faltan restricciones de unicidad en los nombres de `Gym`, `Muscle` y `Exercise`.
- Falta validar el formato de `series_data`.

**API**
- **`video_url` siempre vuelve `null`.** `ExerciseInBlockSerializer.get_video_url` (`gym_tracker/serializer.py:146`) espera `context['gym']`, y ninguna vista lo pasa. Hay que pasar el gym de la rutina.
- **Consultas N+1 al leer rutinas.** Agregar `select_related('gym', 'staff', 'person')` y `prefetch_related('blocks__exercise__muscle', 'blocks__exercise__customexercise')`.
- **No hay paginación.** Configurar una por defecto en `REST_FRAMEWORK`.

**Permisos y validaciones de rutinas y videos**
- **Videos de ejercicios estándar.** Hoy se puede asignar un video a un ejercicio propio, incluso de otro gym (`gym_tracker/views.py:164`). Validar que el ejercicio sea estándar.
- **Un ADMIN que crea una rutina queda guardado como `staff`** (`gym_tracker/views.py:269`), aunque el campo está pensado para STAFF.
- **Acceso tras dejar el gym.** Un PERSON o STAFF que deja un gym sigue viendo sus rutinas de ese gym, porque el detalle no chequea la membresía.
- **Editar una rutina vuelve a validar la membresía del socio** (`gym_tracker/views.py:284`). Si el socio dejó el gym, la rutina ya no se puede ni renombrar.
- **Chequeos que nunca se ejecutan.** Los de "cambio de gym" en `gym_tracker/views.py:125` y `:280` no corren, porque `gym` es de solo lectura al editar.

### P2: mantenimiento

**Backend**
- **Migraciones `gym_tracker` 0001–0003.** Son restos de un modelo `Task` de tutorial y se pueden aplastar con squash. Con cuidado: ya están aplicadas.
- **`GetAllRoutinesView` duplica el listado de rutinas** (`gym_tracker/views.py:299`). Pasarla a un `@action` de `RoutineViewSet` o eliminarla.
- **`LANGUAGE_CODE` es `en-us`**, pero todos los mensajes de la API están en español.

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

**Infra**
- **CI**, por ejemplo con GitHub Actions: `python manage.py test`, `npm run lint` y `npm run build`.
- **Producción:**
  - Resolver los warnings de `manage.py check --deploy`: HTTPS, HSTS y cookies seguras.
  - Pasar a PostgreSQL.
  - Configurar `STATIC_ROOT`.
  - Usar un servidor WSGI/ASGI como gunicorn o uvicorn.
  - Si se usa auth por sesión, configurar `CSRF_TRUSTED_ORIGINS`.
