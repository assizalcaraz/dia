# Módulo: `sessions.py`

**Ubicación**: `cli/dia_cli/sessions.py`  
**Propósito**: Gestión de sesiones (generación de IDs, búsqueda de sesión activa).

---

## Funciones Públicas

### `next_session_id(day_id: str, sessions_path: Path) -> str`

Genera el siguiente ID de sesión para un día específico.

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD` (ej: `"2026-01-18"`).
- `sessions_path` (Path): Ruta al archivo `sessions.ndjson`.

**Retorna**: `str` — ID de sesión en formato `S01`, `S02`, etc.

**Comportamiento**:
- Lee todas las sesiones del día desde `sessions.ndjson`.
- Cuenta cuántas sesiones ya existen para ese día (incluyendo `SessionStarted` y `SessionStartedAfterDayClosed`).
- Retorna el siguiente número secuencial (S01, S02, S03, etc.).

**Nota**: `/dia` permite múltiples sesiones por día sin restricciones. Los IDs se generan secuencialmente.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.sessions import next_session_id

sessions_path = Path("/ruta/data/index/sessions.ndjson")
day = "2026-01-18"
session_id = next_session_id(day, sessions_path)
# Retorna "S01", "S02", etc.
```

---

### `current_session(events_path: Path, repo_path: Optional[str] = None) -> Optional[dict[str, Any]]`

Encuentra la sesión activa actual (última sesión iniciada sin cerrar).

**Parámetros**:
- `events_path` (Path): Ruta al archivo `events.ndjson`.
- `repo_path` (Optional[str]): Ruta del repositorio. Si se especifica, filtra por repo. Si es `None`, retorna la última sesión activa de cualquier repo.

**Retorna**: `Optional[dict[str, Any]]` — Evento `SessionStarted` o `SessionStartedAfterDayClosed` de la sesión activa, o `None` si no hay sesión activa.

**Comportamiento**:
1. Lee todos los eventos de `events.ndjson`.
2. Identifica eventos `SessionStarted`, `SessionStartedAfterDayClosed` y `SessionEnded`.
3. Construye un diccionario de sesiones con su estado (iniciada/cerrada).
4. Retorna la última sesión iniciada sin `SessionEnded` asociado.
5. Si se especifica `repo_path`, filtra por la ruta del repo.

**Nota**: Maneja tanto `SessionStarted` como `SessionStartedAfterDayClosed` como eventos de inicio de sesión válidos.

**Estructura del retorno**:
```python
{
    "event_id": "evt_...",
    "ts": "2026-01-18T10:00:00-03:00",
    "type": "SessionStarted",
    "session": {
        "day_id": "2026-01-18",
        "session_id": "S01",
        "intent": "...",
        "dod": "...",
        "mode": "it"
    },
    "actor": {...},
    "project": {...},
    "repo": {...},
    "payload": {...}
}
```

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.sessions import current_session

events_path = Path("/ruta/data/index/events.ndjson")

# Sesión activa de cualquier repo
session = current_session(events_path)
if session:
    print(f"Sesión activa: {session['session']['session_id']}")

# Sesión activa de un repo específico
repo = "/ruta/al/repo"
session = current_session(events_path, repo_path=repo)
if session:
    print(f"Sesión activa en {repo}: {session['session']['session_id']}")
```

---

## Dependencias

- **Módulo interno**: `utils.read_json_lines` (para leer eventos NDJSON)

---

## Notas de Implementación

- `next_session_id` lee `sessions.ndjson` para contar sesiones existentes. Si el archivo no existe o está vacío, retorna `S01`.
- `current_session` lee `events.ndjson` completo y construye el estado de sesiones en memoria. Esto puede ser lento con muchos eventos, pero es suficiente para v0.1.
- La búsqueda de sesión activa es por orden inverso (más reciente primero), retornando la primera sesión sin cerrar encontrada.

---

## Referencias

- [Guía de `dia start`](../../guides/dia-start.md)
- [Guía de `dia end`](../../guides/dia-end.md)
- [Módulo `utils`](utils.md)
- [Documentación de módulos CLI](README.md)
