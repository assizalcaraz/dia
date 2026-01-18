# Documentación de Endpoints API

**Versión**: v0.1  
**Última actualización**: 2026-01-18

Esta documentación describe todos los endpoints disponibles en la API Django de `/dia`.

---

## Base URL

Todos los endpoints están bajo el prefijo `/api/`:

```
http://localhost:8000/api/
```

---

## Endpoints de Sesiones

### `GET /api/sessions/`

Retorna lista de todas las sesiones.

**Respuesta**:
```json
{
  "sessions": [
    {
      "day_id": "2026-01-18",
      "session_id": "S01",
      "intent": "Implementar feature X",
      "dod": "Tests pasan",
      "mode": "feat",
      "start_ts": "2026-01-18T10:00:00-03:00",
      "end_ts": "2026-01-18T12:30:00-03:00",
      "result": "completed",
      "repo": "/ruta/repo",
      "project": "proyecto",
      "actor": "usuario",
      "started_after_close": false
    }
  ]
}
```

**Notas**:
- Las sesiones están ordenadas por `start_ts` descendente (más recientes primero)
- `end_ts` puede ser `null` si la sesión está activa
- `started_after_close` indica si la sesión comenzó después de cerrar el día

---

### `GET /api/sessions/current/`

Retorna la sesión activa actual (sin `end_ts`).

**Respuesta**:
```json
{
  "session": {
    "day_id": "2026-01-18",
    "session_id": "S02",
    "intent": "Arreglar bug Y",
    "dod": "Bug resuelto",
    "mode": "fix",
    "start_ts": "2026-01-18T14:00:00-03:00",
    "end_ts": null,
    "result": null,
    "repo": "/ruta/repo",
    "project": "proyecto",
    "actor": "usuario",
    "started_after_close": false
  }
}
```

**Notas**:
- Retorna `{"session": null}` si no hay sesión activa
- Solo retorna la sesión más reciente sin `end_ts`

---

## Endpoints de Eventos

### `GET /api/events/recent/`

Retorna eventos recientes del sistema.

**Query params**:
- `limit` (default: 20): número máximo de eventos a retornar

**Ejemplo**:
```bash
curl http://localhost:8000/api/events/recent/?limit=10
```

**Respuesta**:
```json
{
  "events": [
    {
      "event_id": "evt_...",
      "type": "SessionStarted",
      "ts": "2026-01-18T10:00:00-03:00",
      "session": {...},
      "payload": {...},
      "links": [...]
    }
  ]
}
```

**Notas**:
- Los eventos están ordenados por timestamp (más recientes al final)
- Retorna los últimos `limit` eventos

---

## Endpoints de Métricas

### `GET /api/metrics/`

Retorna métricas generales del sistema.

**Respuesta**:
```json
{
  "total_sessions": 42,
  "commit_suggestions": 15,
  "total_events": 1234
}
```

**Notas**:
- `commit_suggestions`: número de eventos `CommitSuggestionIssued`
- `total_events`: total de eventos en el sistema

---

## Endpoints de Resúmenes

### `GET /api/summaries/`

Retorna lista de resúmenes con filtros opcionales.

**Query params**:
- `day_id` (opcional): filtrar por día específico
- `mode` (opcional): filtrar por modo (`rolling` o `nightly`)
- `limit` (opcional): limitar número de resultados

**Ejemplo**:
```bash
curl "http://localhost:8000/api/summaries/?day_id=2026-01-18&mode=rolling&limit=10"
```

**Respuesta**:
```json
{
  "summaries": [
    {
      "summary_id": "rolling_20260118_120000",
      "ts": "2026-01-18T12:00:00-03:00",
      "session": {
        "day_id": "2026-01-18",
        "session_id": "S01"
      },
      "payload": {
        "mode": "rolling",
        "window_start": "2026-01-18T10:00:00-03:00",
        "window_end": "2026-01-18T12:00:00-03:00",
        "content": "..."
      }
    }
  ]
}
```

**Notas**:
- Los resúmenes están ordenados por timestamp descendente
- Si no se especifica `day_id`, retorna resúmenes de todos los días

---

### `GET /api/summaries/latest/`

Retorna el último resumen rolling del día especificado.

**Query params**:
- `day_id` (requerido): día a consultar
- `mode` (opcional, default: `"rolling"`): modo del resumen

**Ejemplo**:
```bash
curl "http://localhost:8000/api/summaries/latest/?day_id=2026-01-18&mode=rolling"
```

**Respuesta**:
```json
{
  "summary": {
    "summary_id": "rolling_20260118_120000",
    "ts": "2026-01-18T12:00:00-03:00",
    "session": {...},
    "payload": {...}
  }
}
```

**Notas**:
- Retorna `{"summary": null}` si no hay resumen para el día/modo especificado
- Retorna el resumen más reciente según timestamp

---

### `GET /api/summaries/<day_id>/list/`

Lista resúmenes disponibles para un día específico.

**Parámetros de ruta**:
- `day_id` (string): ID del día (formato `YYYY-MM-DD`)

**Ejemplo**:
```bash
curl http://localhost:8000/api/summaries/2026-01-18/list/
```

**Respuesta**:
```json
{
  "summaries": [
    {
      "summary_id": "rolling_20260118_120000",
      "mode": "rolling",
      "timestamp": "20260118_120000",
      "assessment": "ON_TRACK",
      "ts": "2026-01-18T12:00:00-03:00"
    },
    {
      "summary_id": "nightly_20260118_235959",
      "mode": "nightly",
      "timestamp": "20260118_235959",
      "assessment": "ON_TRACK",
      "ts": "2026-01-18T23:59:59-03:00"
    }
  ]
}
```

**Notas**:
- Los resúmenes están ordenados por timestamp descendente
- `assessment` puede ser: `"ON_TRACK"`, `"OFF_TRACK"`, `"BLOCKED"`, o `"UNKNOWN"`
- Retorna lista vacía si no hay resúmenes para el día

---

### `GET /api/summaries/<day_id>/<summary_id>/content/`

Retorna contenido markdown de un resumen específico.

**Parámetros de ruta**:
- `day_id` (string): ID del día (formato `YYYY-MM-DD`)
- `summary_id` (string): ID del resumen (sin extensión)

**Ejemplo**:
```bash
curl http://localhost:8000/api/summaries/2026-01-18/rolling_20260118_120000/content/
```

**Respuesta**:
```json
{
  "day_id": "2026-01-18",
  "summary_id": "rolling_20260118_120000",
  "content": "# Resumen Rolling\n\n..."
}
```

**Notas**:
- Retorna error 404 si el resumen no existe
- El contenido es markdown puro

---

## Endpoints de Documentación

### `GET /api/docs/list/`

Lista estructura de documentación (árbol recursivo).

**Respuesta**:
```json
{
  "tree": [
    {
      "name": "modules",
      "type": "directory",
      "path": "modules",
      "children": [
        {
          "name": "api",
          "type": "directory",
          "path": "modules/api",
          "children": [
            {
              "name": "endpoints.md",
              "type": "file",
              "path": "modules/api/endpoints.md"
            }
          ]
        }
      ]
    }
  ]
}
```

**Notas**:
- Estructura recursiva de directorios y archivos
- Solo incluye archivos `.md`
- Ignora archivos y directorios ocultos (que empiezan con `.`)

---

### `GET /api/docs/<path>/`

Retorna contenido markdown de un documento específico.

**Parámetros de ruta**:
- `path` (string): Ruta relativa del documento desde `docs/`

**Ejemplo**:
```bash
curl http://localhost:8000/api/docs/modules/api/endpoints.md/
```

**Respuesta**:
```json
{
  "path": "modules/api/endpoints.md",
  "content": "# Documentación de Endpoints API\n\n..."
}
```

**Notas**:
- Retorna error 400 si la ruta es inválida (intenta salir de `docs/`)
- Retorna error 404 si el documento no existe
- Retorna error 400 si el archivo no es `.md`
- El contenido es markdown puro

---

## Endpoints de Días

### `GET /api/day/closed/`

Verifica si un día está cerrado (busca evento `DayClosed`).

**Query params**:
- `day_id` (requerido): ID del día a consultar

**Ejemplo**:
```bash
curl "http://localhost:8000/api/day/closed/?day_id=2026-01-18"
```

**Respuesta**:
```json
{
  "day_id": "2026-01-18",
  "closed": true,
  "closed_at": "2026-01-18T23:59:59-03:00"
}
```

**Notas**:
- `closed`: booleano indicando si el día está cerrado
- `closed_at`: timestamp del cierre (si está cerrado), `null` si no está cerrado
- Retorna error 400 si no se proporciona `day_id`

---

### `GET /api/day/today/`

Retorna información del día actual: sesiones, estado, etc.

**Respuesta**:
```json
{
  "day_id": "2026-01-18",
  "sessions_count": 3,
  "sessions": [
    {
      "session_id": "S01",
      "start_ts": "2026-01-18T10:00:00-03:00",
      "end_ts": "2026-01-18T12:30:00-03:00",
      "elapsed_minutes": 150,
      "intent": "Implementar feature X",
      "dod": "Tests pasan",
      "repo": "/ruta/repo",
      "active": false,
      "started_after_close": false
    },
    {
      "session_id": "S02",
      "start_ts": "2026-01-18T14:00:00-03:00",
      "end_ts": null,
      "elapsed_minutes": 45,
      "intent": "Arreglar bug Y",
      "dod": "Bug resuelto",
      "repo": "/ruta/repo",
      "active": true,
      "started_after_close": false
    }
  ],
  "closed": false,
  "closed_at": null
}
```

**Notas**:
- `day_id`: calculado automáticamente como fecha actual en zona horaria local
- `sessions_count`: número de sesiones iniciadas (incluyendo `SessionStartedAfterDayClosed`)
- `sessions`: lista de sesiones del día con `elapsed_minutes` calculado
- `elapsed_minutes`: tiempo transcurrido en minutos (calculado hasta ahora si la sesión está activa)
- `active`: `true` si la sesión no tiene `end_ts`
- `closed`: indica si el día está cerrado
- Las sesiones están ordenadas por `start_ts` descendente

---

## Endpoints de Bitácoras

### `GET /api/jornada/<day_id>/`

Retorna contenido de bitácora de jornada específica.

**Parámetros de ruta**:
- `day_id` (string): ID del día (formato `YYYY-MM-DD`)

**Ejemplo**:
```bash
curl http://localhost:8000/api/jornada/2026-01-18/
```

**Respuesta**:
```json
{
  "day_id": "2026-01-18",
  "content": "# Jornada 2026-01-18\n\n..."
}
```

**Notas**:
- Retorna error 404 si la bitácora no existe
- El contenido es markdown puro
- El archivo se busca en `data/bitacora/{day_id}.md`

---

## Endpoints de Capturas

### `GET /api/captures/recent/`

Retorna capturas recientes (`CaptureCreated` y `CaptureReoccurred`).

**Query params**:
- `limit` (default: 20): número máximo de resultados

**Ejemplo**:
```bash
curl http://localhost:8000/api/captures/recent/?limit=10
```

**Respuesta**:
```json
{
  "captures": [
    {
      "event_id": "evt_...",
      "type": "CaptureCreated",
      "ts": "2026-01-18T15:15:00-03:00",
      "session": {
        "day_id": "2026-01-18",
        "session_id": "S01"
      },
      "payload": {
        "kind": "error",
        "title": "deploy staging falla",
        "error_hash": "...",
        "artifact_ref": "artifacts/captures/2026-01-18/S01/cap_...txt"
      },
      "links": []
    },
    {
      "event_id": "evt_...",
      "type": "CaptureReoccurred",
      "ts": "2026-01-18T16:00:00-03:00",
      "session": {...},
      "payload": {
        "kind": "error",
        "title": "deploy staging falla",
        "error_hash": "...",
        "original_event_id": "evt_...",
        "artifact_ref": "..."
      },
      "links": []
    }
  ]
}
```

**Notas**:
- Las capturas están ordenadas por timestamp descendente (más recientes primero)
- Incluye tanto `CaptureCreated` como `CaptureReoccurred`
- `CaptureReoccurred` incluye `original_event_id` que referencia al error original

---

### `GET /api/captures/errors/open/`

Retorna lista de errores sin fix (último `CaptureCreated` sin `FixLinked` por sesión).

**Ejemplo**:
```bash
curl http://localhost:8000/api/captures/errors/open/
```

**Respuesta**:
```json
{
  "errors": [
    {
      "event_id": "evt_...",
      "ts": "2026-01-18T15:15:00-03:00",
      "session": {
        "day_id": "2026-01-18",
        "session_id": "S01"
      },
      "title": "deploy staging falla",
      "error_hash": "...",
      "artifact_ref": "artifacts/captures/2026-01-18/S01/cap_...txt",
      "links": []
    }
  ]
}
```

**Lógica de detección**:
- Usa `error_event_id` para asociar `FixLinked` a `CaptureCreated` específicos
- Un error está fijado solo si tiene un `FixLinked` con su `error_event_id` específico
- Esto permite que errores con el mismo `error_hash` (errores repetidos) tengan fixes independientes
- Solo muestra el error más reciente por sesión

**Notas**:
- Los errores están ordenados por timestamp descendente
- Solo incluye errores de tipo `CaptureCreated` (no `CaptureReoccurred`)
- Un error está "abierto" si no tiene un `FixLinked` asociado a su `event_id` específico

---

## Códigos de Estado HTTP

- `200 OK`: Solicitud exitosa
- `400 Bad Request`: Parámetros inválidos o faltantes
- `404 Not Found`: Recurso no encontrado
- `500 Internal Server Error`: Error del servidor

---

## Formato de Respuestas

Todas las respuestas exitosas retornan JSON con la siguiente estructura:

```json
{
  "key": "value",
  "array": [...],
  "nested": {
    "object": "..."
  }
}
```

Los errores retornan:

```json
{
  "error": "Mensaje de error descriptivo"
}
```

---

## Notas de Implementación

### Ordenamiento

- **Sesiones**: Ordenadas por `start_ts` descendente (más recientes primero)
- **Eventos**: Ordenados por timestamp (más recientes al final del array)
- **Capturas**: Ordenadas por `ts` descendente (más recientes primero)
- **Resúmenes**: Ordenados por timestamp descendente

### Filtrado

- Los endpoints que soportan filtros (`day_id`, `mode`, `limit`) aplican los filtros en el orden especificado
- Los filtros son acumulativos (se aplican todos si están presentes)

### Timestamps

- Todos los timestamps están en formato ISO 8601 con zona horaria
- Ejemplo: `"2026-01-18T15:15:00-03:00"`

---

## Referencias

- [Documentación de componentes UI](../components/README.md) - Componentes que usan estos endpoints
- [Manual de captura de errores](../../manual/CAPTURA_ERRORES.md) - Uso de endpoints de capturas
- [Estructura NDJSON](../../specs/NDJSON.md) - Formato de eventos

---

**Última actualización**: 2026-01-18
