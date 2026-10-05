# CONTEXTO DEL PROYECTO: Generador de Exámenes desde JSON

> Este archivo es la fuente de verdad. Las decisiones de aquí NO se discuten de nuevo.
> Ideas nuevas van a la sección "Ideas futuras" al final, no se implementan.

## 1. Objetivo
Aplicación web multiusuario. El usuario organiza **carpetas anidadas**, sube un **JSON estructurado** dentro de una carpeta y este se convierte en un **examen**. Luego rinde el examen (con filtros y aleatorización), se califica en el servidor y queda el historial de intentos.

## 2. Stack (fijo)
| Capa | Tecnología |
|---|---|
| Backend | Python 3.11+, FastAPI, Uvicorn |
| ORM / migraciones | SQLAlchemy 2.0 (tipado), Alembic |
| Validación | Pydantic v2, pydantic-settings |
| Base de datos | PostgreSQL en **Neon** (sin Docker) |
| Frontend | **React + Vite + React Router**, estilos con Tailwind |
| Auth | Email + contraseña (argon2), **JWT** en `Authorization: Bearer` |
| Despliegue | Backend en **Render**, frontend en **Vercel** |
| Pruebas | pytest + httpx (solo lógica crítica) |

No se usa Docker ni MCP. Todo se despliega por `git push`.

## 3. Estructura del repo (monorepo)
```
examen-app/
├── CONTEXTO.md
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── security.py          # hash y JWT
│   │   ├── deps.py              # get_db, get_current_user
│   │   ├── routers/             # auth.py, carpetas.py, examenes.py, intentos.py
│   │   └── services/            # importador.py, generador.py, calificador.py
│   ├── alembic/
│   ├── tests/
│   ├── ejemplos/banco_ejemplo.json
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/ (pages/, components/, api/, context/)
    ├── package.json
    └── .env.example
```

## 4. Formato del JSON de entrada
```json
{
  "titulo": "Bases de Datos I",
  "preguntas": [
    {
      "enunciado": "¿Qué cláusula filtra grupos en SQL?",
      "tipo": "opcion_unica",
      "tema": "SQL",
      "dificultad": "media",
      "puntaje": 2,
      "opciones": [
        { "texto": "WHERE", "correcta": false },
        { "texto": "HAVING", "correcta": true },
        { "texto": "GROUP BY", "correcta": false }
      ]
    }
  ]
}
```
- `tipo`: `opcion_unica` | `opcion_multiple` | `verdadero_falso`
- `dificultad`: `facil` | `media` | `dificil`
- `tema` y `dificultad` son opcionales; `puntaje` por defecto 1.

### Reglas de validación
- `titulo`: no vacío, máx. 150. `preguntas`: mínimo 1.
- `enunciado` no vacío; `puntaje` > 0.
- `opcion_unica`: ≥2 opciones y exactamente 1 correcta.
- `opcion_multiple`: ≥2 opciones y ≥1 correcta.
- `verdadero_falso`: exactamente 2 opciones ("Verdadero", "Falso") y 1 correcta.
- Sin opciones duplicadas en una misma pregunta.
- Errores con posición: `preguntas[3]: debe haber exactamente una opción correcta`.
- Archivo máx. 2 MB, JSON válido, UTF-8. Respuesta 422 si falla.

## 4.1 Modelo de datos (PostgreSQL)
```
usuario(id, email UNIQUE, nombre, password_hash, creado_en)
carpeta(id, usuario_id FK, padre_id FK→carpeta NULL, nombre, creado_en)
  UNIQUE NULLS NOT DISTINCT (usuario_id, padre_id, nombre)
  padre_id ON DELETE CASCADE
examen(id, usuario_id FK, carpeta_id FK ON DELETE CASCADE, titulo, creado_en)
tema(id, nombre UNIQUE)                       -- normalizado con trim, se reutiliza
pregunta(id, examen_id FK CASCADE, tema_id FK NULL, enunciado, tipo, dificultad, puntaje NUMERIC(4,2))
opcion(id, pregunta_id FK CASCADE, texto, es_correcta BOOLEAN)
intento(id, examen_id FK, usuario_id FK, estado, puntaje_total, puntaje_maximo, iniciado_en, rendido_en NULL)
intento_pregunta(intento_id FK, pregunta_id FK, orden)   -- PK compuesta
respuesta(intento_id FK, pregunta_id FK, opcion_id FK)   -- PK compuesta
```
- CHECK en `tipo`, `dificultad` e `intento.estado` (`en_curso` | `finalizado`).
- Índices: `carpeta(usuario_id, padre_id)`, `examen(carpeta_id)`, `pregunta(examen_id)`, `opcion(pregunta_id)`, `intento(examen_id)`.
- Tablas creadas **solo con Alembic**, nunca con `create_all`.
- Importación en **una sola transacción**: si falla algo, no se guarda nada.
- Árbol y breadcrumb de carpetas con **CTE recursiva**.

## 5. Reglas de negocio (no negociables)
1. **Autorización por propietario**: toda consulta filtra por `usuario_id`. Si un recurso no es del usuario, responder 404.
2. **Nunca enviar `es_correcta`** al cliente mientras el intento esté `en_curso`.
3. **Calificación solo en el servidor**:
   - `opcion_unica` / `verdadero_falso`: puntaje completo si la opción marcada es la correcta.
   - `opcion_multiple`: puntaje completo solo si el conjunto marcado = conjunto de correctas (todo o nada).
   - Sin responder = 0.
4. Validar que cada `opcion_id` pertenezca a su pregunta y cada pregunta al intento.
5. Un intento `finalizado` no se puede volver a enviar.
6. El orden de las opciones se aleatoriza al mostrar el intento.
7. Si el usuario pide más preguntas de las disponibles con sus filtros: 422 indicando cuántas hay.
8. Contraseñas con argon2; JWT con expiración (ej. 24 h); CORS solo con el dominio de Vercel.

## 6. Endpoints
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro` | Crea usuario |
| POST | `/auth/login` | Devuelve JWT |
| GET | `/auth/me` | Usuario actual |
| GET | `/carpetas?padre_id=` | Subcarpetas y exámenes de una carpeta (sin `padre_id` = raíz) |
| POST | `/carpetas` | Crea carpeta `{nombre, padre_id?}` |
| PATCH | `/carpetas/{id}` | Renombrar (mover queda fuera de alcance) |
| DELETE | `/carpetas/{id}` | Borra en cascada |
| GET | `/carpetas/{id}/ruta` | Breadcrumb (CTE recursiva) |
| POST | `/carpetas/{id}/examenes/importar` | Sube JSON (multipart), valida y guarda |
| GET | `/examenes/{id}` | Resumen: título, temas, cantidad por dificultad |
| DELETE | `/examenes/{id}` | Borra examen |
| POST | `/examenes/{id}/intentos` | Crea intento `{cantidad, temas?, dificultad?, aleatorio}` y devuelve preguntas SIN `es_correcta` |
| POST | `/intentos/{id}/enviar` | Recibe `{respuestas:[{pregunta_id, opciones_ids}]}`, califica y guarda |
| GET | `/intentos/{id}` | Resultado detallado (solo si está finalizado) |
| GET | `/examenes/{id}/intentos` | Historial del usuario para ese examen |

## 7. Despliegue
- **Neon**: usar la cadena *pooled* para la app y la *directa* para Alembic. Siempre `sslmode=require`.
- **Render** (Web Service, root `backend/`): build `pip install -r requirements.txt`; start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Migraciones con `alembic upgrade head` ejecutado manualmente.
- **Vercel** (root `frontend/`): framework Vite. La conexión de producción queda definida mediante **`/api` con rewrite hacia Render**. La configuración está en `frontend/vercel.json`, junto a `package.json`:
  - `/api/:path*` → `https://examen-app-pudc.onrender.com/:path*`.
  - `/(.*)` → `/index.html` para React Router, después del rewrite de la API.
  - El navegador llama a `https://examen-app-lyart.vercel.app/api/health`; Vercel reenvía a `https://examen-app-pudc.onrender.com/health`. Esta conexión usa el mismo origen del frontend y no requiere CORS entre el navegador y Render.
- Variables:
  - Backend: `DATABASE_URL`, `SECRET_KEY`, `CORS_ORIGINS`, `ACCESS_TOKEN_MINUTES`
  - En Render, el **valor** de `CORS_ORIGINS` debe ser la lista JSON `["https://examen-app-lyart.vercel.app"]`, sin anteponer `CORS_ORIGINS=`. Una URL sola impide arrancar el backend. `ACCESS_TOKEN_MINUTES=1440` (guardar solo `1440` como valor).
  - Frontend en Vercel: `VITE_API_URL=/api`. `App.jsx` usa `import.meta.env.VITE_API_URL || "/api"` y llama a `${API}/health`. No configurar la URL completa de Render para esta conexión. Los cambios de variables `VITE_` requieren un nuevo build y despliegue.
- **Local**: `frontend/.env` contiene `VITE_API_URL=http://localhost:8000`; el navegador llama directamente a FastAPI, que permite CORS desde `http://localhost:5173`.
- **Verificación de producción completada**: `/api/health` respondió HTTP 200 con `{"status":"ok","database":"ok"}` y la página principal mostró `API: ok | BD: ok` tras Ctrl+Shift+R. Los dos archivos de conexión se subieron en el commit `d5632b8` (`usar rewrite /api`).
- Render gratis se "duerme": el frontend debe mostrar estado de carga/reintento en la primera petición.
- Ninguna credencial en el repo (`.env` en `.gitignore`).

## 8. Fuera de alcance (v1)
Mover carpetas, exportar a PDF, dashboard Power BI, compartir exámenes entre usuarios, recuperación de contraseña, edición de preguntas en la web, temporizador, roles/admin.

## 9. Plan por rebanadas
**Estado verificado el 5 de octubre de 2026: rebanadas 0 y 1 terminadas y funcionando en producción.**

- Migración `7b124df901ac` aplicada en Neon mediante `DATABASE_URL_DIRECT`; creó solo `usuario` y la tabla estaba vacía antes de las pruebas.
- Registro, login, `/auth/me`, rutas protegidas y sesión tras recarga comprobados en local y en Vercel → `/api` → Render → Neon.
- Email duplicado y contraseña incorrecta comprobados en la interfaz local; token inválido devuelve 401. Pruebas del backend: 16 aprobadas; lint y build de React aprobados.
- Token JWT Bearer en `sessionStorage`, restauración con `/auth/me` y limpieza de sesión al expirar o recibir 401. El commit de implementación es `bde1ba4`.
- Se rotaron las conexiones de Neon y la clave JWT; los secretos permanecen en los entornos y no en Git. Las pruebas integradas crearon dos cuentas sintéticas con emails `prueba-local-*` y `prueba-vercel-*`.

Cada rebanada = BD + backend + frontend de UNA funcionalidad, funcionando de punta a punta. Al terminar: pruebo, `git commit` y abro **chat nuevo**.

| # | Rebanada | Criterio de aceptación |
|---|---|---|
| 0 | Esqueleto | `/health` responde en Render; React en Vercel llama a `/health`; conexión a Neon OK; migración inicial vacía aplicada |
| 1 | Usuarios | Registro, login, `/auth/me`, rutas protegidas en React, CORS correcto |
| 2 | Carpetas | Crear, listar, renombrar, borrar y anidar; breadcrumb; nombre único por padre |
| 3 | Importar examen | Subir JSON dentro de una carpeta; 422 con mensajes por pregunta; temas sin duplicar; transacción única; pruebas del importador |
| 4 | Rendir examen | Crear intento con filtros, mostrar preguntas sin `es_correcta`, enviar, calificar y mostrar resultado; pruebas del calificador (3 tipos) |
| 5 | Historial | Lista de intentos por examen y detalle por pregunta |
| 6 | Pulido | Diseño con skill `frontend-design`, estados de carga/error, README con capturas |

Con la rebanada 4 ya existe un producto usable.

## 10. Reglas de trabajo con la IA (ahorro de cuota)
- Un chat por rebanada. Pego este archivo + la tarea.
- Pedir solo archivos nuevos o modificados, completos, y cómo probarlos.
- Si hay un error: pegar solo el traceback y el archivo implicado.
- No rediseñar a mitad de rebanada; las ideas van abajo.
- Lo mecánico (crear repos, Neon, Render, Vercel, variables) lo hago yo a mano.
- Estilos mínimos hasta la rebanada 6.
- Commits pequeños; si algo sale mal, `git revert` en vez de pedir arreglos largos.

## 11. Plantilla de prompt por rebanada
```
Contexto: [pegar CONTEXTO.md completo]
Estado actual: rebanadas 0 a N-1 terminadas y funcionando.
Tarea: implementa la rebanada N ([nombre]).
Respeta todo lo decidido en el contexto. No cambies el diseño.
Entrega: solo archivos nuevos o modificados (completos, con su ruta),
migración de Alembic si hay cambios de BD, y pasos para probarlo.
```

## 12. Ideas futuras (no implementar ahora)
-
