# ROL
Eres un ingeniero backend senior. Vas a construir, paso a paso, una aplicación web de generación de exámenes a partir de un archivo JSON. Código limpio, tipado, comentado en español y listo para correr.

# OBJETIVO
Aplicación web donde el usuario sube un archivo JSON con un banco de preguntas. El sistema lo valida, lo guarda en una base de datos relacional, genera exámenes a partir de ese banco, los muestra, califica las respuestas en el servidor y guarda el historial de intentos.

# STACK (obligatorio)
- Python 3.11+, FastAPI, Uvicorn
- SQLAlchemy 2.0 (estilo declarativo tipado) + Alembic para migraciones
- PostgreSQL (docker-compose para desarrollo)
- Pydantic v2 para validar el JSON y los DTOs
- Frontend simple: HTML + CSS + JavaScript vanilla (fetch), servido por FastAPI en /static
- pytest + httpx para pruebas
- Configuración por variables de entorno (.env, pydantic-settings)

# FORMATO DEL JSON DE ENTRADA
```json
{
  "banco": "Bases de Datos I",
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
Tipos soportados: `opcion_unica`, `opcion_multiple`, `verdadero_falso`.
Dificultades permitidas: `facil`, `media`, `dificil`.

## Reglas de validación (Pydantic)
- `banco`: string no vacío, máx. 150 caracteres.
- `preguntas`: lista con al menos 1 elemento.
- `enunciado`: no vacío.
- `puntaje`: número > 0 (por defecto 1).
- `opcion_unica`: mínimo 2 opciones y EXACTAMENTE 1 correcta.
- `opcion_multiple`: mínimo 2 opciones y al menos 1 correcta.
- `verdadero_falso`: EXACTAMENTE 2 opciones ("Verdadero" y "Falso") y 1 correcta.
- Rechazar opciones duplicadas dentro de la misma pregunta.
- Los errores de validación deben indicar la posición de la pregunta (ej. "preguntas[3]: debe haber exactamente una opción correcta").

# MODELO RELACIONAL (PostgreSQL)
Tablas: `banco`, `tema`, `pregunta`, `opcion`, `examen`, `examen_pregunta`, `intento`, `respuesta`.

- `banco(id, nombre, creado_en)`
- `tema(id, nombre UNIQUE)`: se normaliza (trim) y se reutiliza si ya existe.
- `pregunta(id, banco_id FK ON DELETE CASCADE, tema_id FK, enunciado, tipo, dificultad, puntaje NUMERIC(4,2))`
- `opcion(id, pregunta_id FK ON DELETE CASCADE, texto, es_correcta BOOLEAN)`
- `examen(id, banco_id FK, titulo, generado_en)`
- `examen_pregunta(examen_id FK, pregunta_id FK, orden, PK compuesta)`: relación N:M.
- `intento(id, examen_id FK, puntaje_total NUMERIC(5,2), puntaje_maximo NUMERIC(5,2), rendido_en)`
- `respuesta(intento_id FK, pregunta_id FK, opcion_id FK, PK compuesta)`

Requisitos:
- Restricciones CHECK en `tipo` y `dificultad`.
- Índices en `pregunta(banco_id)`, `pregunta(tema_id)` y `opcion(pregunta_id)`.
- La importación debe ocurrir en UNA sola transacción: si algo falla, no se guarda nada.
- Crear las tablas mediante migraciones de Alembic, no con `create_all`.

# ENDPOINTS
| Método | Ruta | Descripción |
|---|---|---|
| POST | `/bancos/importar` | Recibe archivo `.json` (multipart), valida, inserta y devuelve resumen (nº de preguntas por tema y dificultad) |
| GET | `/bancos` | Lista bancos con cantidad de preguntas |
| GET | `/bancos/{id}/temas` | Temas disponibles en el banco |
| POST | `/examenes` | Body: `banco_id`, `titulo`, `cantidad`, `temas[]` opcional, `dificultad` opcional, `aleatorio` (bool). Genera y guarda el examen |
| GET | `/examenes/{id}` | Devuelve el examen con preguntas y opciones **SIN el campo `es_correcta`** |
| POST | `/examenes/{id}/intentos` | Recibe `{respuestas: [{pregunta_id, opciones_ids: []}]}`, califica y guarda |
| GET | `/intentos/{id}` | Resultado detallado: puntaje, y por pregunta lo marcado, lo correcto y si acertó |
| GET | `/examenes/{id}/intentos` | Historial de intentos del examen |

# REGLAS DE NEGOCIO
- **Generación**: filtrar por banco, temas y dificultad; si `aleatorio` es true usar `ORDER BY random() LIMIT n`. Si hay menos preguntas que `cantidad`, devolver 422 con mensaje claro indicando cuántas hay disponibles.
- **Orden de opciones**: aleatorizar el orden de las opciones al mostrar el examen.
- **Calificación (en el servidor)**:
  - `opcion_unica` y `verdadero_falso`: puntaje completo si la opción marcada es la correcta.
  - `opcion_multiple`: puntaje completo solo si el conjunto marcado coincide exactamente con el conjunto de correctas (todo o nada).
  - Pregunta sin responder = 0 puntos.
- **Seguridad**: el cliente nunca recibe `es_correcta` antes de rendir. Validar que las `opciones_ids` enviadas pertenezcan a la pregunta indicada y que las preguntas pertenezcan al examen.
- Límite de tamaño del archivo (ej. 2 MB) y verificación de que sea JSON válido y UTF-8.

# ESTRUCTURA DE CARPETAS
```
examen-app/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py          # Pydantic: JSON de entrada y DTOs
│   ├── routers/
│   │   ├── bancos.py
│   │   ├── examenes.py
│   │   └── intentos.py
│   └── services/
│       ├── importador.py
│       ├── generador.py
│       └── calificador.py
├── alembic/
├── frontend/
│   ├── index.html          # subir JSON y ver bancos
│   ├── examen.html         # generar y rendir examen
│   ├── resultado.html
│   └── app.js
├── tests/
├── ejemplos/banco_ejemplo.json   # mínimo 12 preguntas de los 3 tipos y 3 temas
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

# FASES (entrega una por una y espera mi confirmación antes de pasar a la siguiente)
1. **Base**: estructura, docker-compose con PostgreSQL, config, conexión y modelos SQLAlchemy + migración inicial de Alembic.
2. **Validación e importación**: schemas Pydantic con todas las reglas, servicio importador transaccional y endpoint `/bancos/importar` con pruebas.
3. **Generación de exámenes**: servicio generador, endpoints de creación y consulta (sin `es_correcta`), con pruebas.
4. **Calificación e historial**: servicio calificador, endpoints de intentos, con pruebas de los 3 tipos de pregunta.
5. **Frontend**: las 3 páginas HTML con JS, mensajes de error claros y diseño sencillo con CSS (responsive).
6. **Cierre**: README con instrucciones de ejecución, ejemplos de uso con curl, y archivo de ejemplo.

# CRITERIOS DE ACEPTACIÓN
- `docker compose up` + `alembic upgrade head` + `uvicorn app.main:app` deja todo funcionando.
- Un JSON inválido devuelve 422 con mensajes que indican la pregunta y el motivo.
- Un JSON válido persiste correctamente y no duplica temas.
- `GET /examenes/{id}` jamás expone respuestas correctas.
- `pytest` pasa con cobertura de importador, generador y calificador.
- Código con type hints, sin credenciales en el repositorio.

# FORMA DE RESPONDER
En cada fase: (1) explica brevemente las decisiones, (2) entrega los archivos completos con su ruta, (3) indica cómo probar lo hecho. No omitas código con comentarios tipo "el resto igual". Si algo es ambiguo, haz una pregunta corta antes de asumir.