# Módulo: `ndjson.py`

**Ubicación**: `cli/dia_cli/ndjson.py`  
**Propósito**: Utilidad para escribir eventos en formato NDJSON (Newline Delimited JSON).

---

## Funciones Públicas

### `append_line(path: Path, payload: dict[str, Any]) -> None`

Agrega un evento al archivo NDJSON (append-only).

**Parámetros**:
- `path` (Path): Ruta del archivo NDJSON (ej: `events.ndjson`).
- `payload` (dict[str, Any]): Objeto JSON a escribir (debe ser serializable).

**Comportamiento**:
1. Crea el directorio padre si no existe.
2. Abre el archivo en modo append (`"a"`).
3. Serializa el payload a JSON en una sola línea.
4. Agrega un salto de línea (`\n`).
5. Escribe al archivo.

**Formato NDJSON**:
- Cada línea es un objeto JSON válido.
- No hay separadores entre objetos (solo newlines).
- El archivo es append-only (no se reescribe).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.ndjson import append_line

events_path = Path("/ruta/data/index/events.ndjson")
event = {
    "event_id": "evt_123",
    "ts": "2026-01-18T10:00:00-03:00",
    "type": "SessionStarted",
    "session": {...},
    "actor": {...},
    "project": {...},
    "repo": {...},
    "payload": {},
    "links": []
}

append_line(events_path, event)
# Agrega una línea al archivo NDJSON
```

---

## Formato NDJSON

**Ejemplo de archivo**:
```json
{"event_id":"evt_001","ts":"2026-01-18T10:00:00-03:00","type":"SessionStarted",...}
{"event_id":"evt_002","ts":"2026-01-18T10:05:00-03:00","type":"RepoBaselineCaptured",...}
{"event_id":"evt_003","ts":"2026-01-18T14:30:00-03:00","type":"SessionEnded",...}
```

**Características**:
- **Append-only**: No se reescribe, solo se agrega al final.
- **Una línea por evento**: Cada objeto JSON está en una sola línea.
- **Sin separadores**: Solo newlines entre objetos.
- **UTF-8**: Codificación estándar.

---

## Dependencias

- **Módulo estándar**: `json` (para serialización)
- **Módulo estándar**: `pathlib` (para rutas)
- **Módulo estándar**: `typing` (para type hints)

---

## Notas de Implementación

- Usa `json.dumps(payload, ensure_ascii=True)` para serializar.
- `ensure_ascii=True` asegura que caracteres no-ASCII se escapen como `\uXXXX`.
- El archivo se abre en modo texto (`"a"`, encoding UTF-8 implícito).
- El directorio padre se crea automáticamente si no existe.

---

## Referencias

- [Estructura NDJSON de eventos](../../specs/NDJSON.md)
- [Módulo `utils`](utils.md) (para leer NDJSON)
- [Documentación de módulos CLI](README.md)
