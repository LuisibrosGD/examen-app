# Rebanada 1: usuarios

## Configuración y migración (PowerShell)

Desde la raíz del repo:

```powershell
cd backend
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Completar `backend/.env` siguiendo `backend/.env.example`:

- `DATABASE_URL`: conexión pooled de Neon con `postgresql+psycopg://`.
- `DATABASE_URL_DIRECT`: conexión direct de Neon para Alembic.
- Conservar los parámetros de seguridad de ambas cadenas de Neon.
- `SECRET_KEY`: clave aleatoria de al menos 32 caracteres, sin compartirla ni subirla.
- `ACCESS_TOKEN_MINUTES=1440`.
- Local: `CORS_ORIGINS=["http://localhost:5173"]`.
- Render: `CORS_ORIGINS=["https://examen-app-lyart.vercel.app"]`.

Para generar una clave nueva:

```powershell
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Ya se generó una clave en el `.env` local; usar una clave propia en Render.
No regenerar la clave en cada arranque: cambiarla invalida los JWT existentes.

Aplicar manualmente la migración en Neon antes de utilizar usuarios:

```powershell
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m alembic current
```

Resultado esperado: `7b124df901ac (head)`. La nueva migración crea únicamente
`usuario`, con email único, hash de contraseña y fecha de creación.

Iniciar el backend:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload --reload-dir app
```

En otra terminal, desde la raíz:

```powershell
cd frontend
npm install
npm run dev
```

Local: `frontend/.env` usa `VITE_API_URL=http://localhost:8000`.
En Vercel permanece `VITE_API_URL=/api` y el rewrite existente.

## Prueba manual

1. Abrir `http://localhost:5173/` sin sesión: debe redirigir a `/login`.
2. Ir a `/registro`. Crear una cuenta con nombre, email y contraseña de 8 a
   128 caracteres. Debe indicar que la cuenta se creó.
3. Registrar el mismo email, incluso cambiando mayúsculas: debe mostrar el
   error de email duplicado.
4. En `/login`, probar una contraseña incorrecta y después la correcta.
5. Tras el login, debe aparecer la página protegida con el nombre y email del
   usuario y el estado del backend. Recargar: la sesión se restaura mediante
   `/auth/me`.
6. Cerrar sesión: debe volver al login y bloquear la ruta `/`.
7. Para comprobar expiración, establecer temporalmente
   `ACCESS_TOKEN_MINUTES=1`, reiniciar el backend e iniciar sesión de nuevo.
   Al expirar el token debe volver al login. Restaurar después el valor 1440.

El token se guarda en `sessionStorage`: persiste al recargar la misma pestaña
y se elimina al cerrar sesión. No hay refresh token en esta rebanada. Un 401
de una petición autenticada limpia la sesión. Una caída de red al restaurar
la sesión muestra un error con reintento sin borrar el token.

## Contratos JSON

`POST /auth/registro`:

```json
{"nombre":"Persona","email":"persona@example.com","password":"UnaClaveSegura123"}
```

Devuelve 201 con `id`, `email`, `nombre` y `creado_en`; nunca devuelve el hash.
Email repetido: 409. Datos inválidos: 422, sin devolver los valores de entrada.

`POST /auth/login`:

```json
{"email":"persona@example.com","password":"UnaClaveSegura123"}
```

Devuelve `access_token`, `token_type="bearer"` y `expires_in` (segundos).
Credenciales incorrectas: 401 con el mismo mensaje para email inexistente o
contraseña equivocada.

`GET /auth/me`: enviar `Authorization: Bearer <access_token>`.
Devuelve solo al usuario identificado por el JWT. Sin token, token inválido,
expirado o usuario inexistente: 401. JWT firmado con HS256; se exigen `sub`,
`iat` y `exp`.

## Pruebas automatizadas

```powershell
cd backend
.\venv\Scripts\python.exe -m pytest -q
cd ../frontend
npm run lint
npm run build
```

Las pruebas de backend utilizan una SQLite temporal creada y desmontada con
las migraciones de Alembic. No tocan Neon ni crean tablas con `create_all`.
Cubren registro, argon2, email normalizado/duplicado, validación, login,
`/auth/me`, usuario aislado, firma/expiración/claims del JWT y CORS.
La ejecución de la migración en PostgreSQL y el recorrido de navegador en
producción se comprueban manualmente con los pasos anteriores.

## Despliegue manual

Antes de desplegar el backend, completar las variables de Render mencionadas
arriba y ejecutar `alembic upgrade head` contra Neon con la conexión directa.
La clave local no se publica. Subir el código mediante git cuando estas
condiciones estén listas; conservar la configuración `/api` de Vercel.
Probar en producción `/registro`, `/login` y `/` siguiendo la misma secuencia.
