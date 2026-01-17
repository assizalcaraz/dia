# Módulo: `utils.py`

**Ubicación**: `cli/dia_cli/utils.py`  
**Propósito**: Utilidades generales (timestamps, lectura de archivos, hashes, búsqueda de errores).

---

## Funciones Públicas

### `now_iso() -> str`

Genera timestamp ISO 8601 con zona horaria.

**Retorna**: `str` — Timestamp en formato `YYYY-MM-DDTHH:MM:SS.ffffff+HH:MM` (ej: `"2026-01-18T10:00:00-03:00"`).

**Ejemplo**:
```python
from dia_cli.utils import now_iso

timestamp = now_iso()
# Retorna: "2026-01-18T10:00:00-03:00"
```

---

### `day_id() -> str`

Genera el ID del día actual en formato ISO.

**Retorna**: `str` — Fecha en formato `YYYY-MM-DD` (ej: `"2026-01-18"`).

**Ejemplo**:
```python
from dia_cli.utils import day_id

day = day_id()
# Retorna: "2026-01-18"
```

---

### `read_json_lines(path: Path) -> Iterable[dict[str, Any]]`

Lee un archivo NDJSON y retorna un iterable de objetos JSON.

**Parámetros**:
- `path` (Path): Ruta del archivo NDJSON.

**Retorna**: `Iterable[dict[str, Any]]` — Iterable de objetos JSON (uno por línea).

**Comportamiento**:
- Si el archivo no existe, retorna un iterable vacío.
- Lee línea por línea, ignorando líneas vacías.
- Cada línea debe ser un JSON válido.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.utils import read_json_lines

events_path = Path("/ruta/data/index/events.ndjson")
for event in read_json_lines(events_path):
    print(event["type"])
```

---

### `write_text(path: Path, content: str) -> None`

Escribe contenido de texto a un archivo.

**Parámetros**:
- `path` (Path): Ruta del archivo.
- `content` (str): Contenido a escribir.

**Comportamiento**:
- Crea el directorio padre si no existe.
- Escribe el contenido en UTF-8.
- Sobrescribe el archivo si existe.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.utils import write_text

file_path = Path("/ruta/archivo.txt")
write_text(file_path, "Contenido del archivo")
```

---

### `read_text(path: Path) -> str`

Lee contenido de texto de un archivo.

**Parámetros**:
- `path` (Path): Ruta del archivo.

**Retorna**: `str` — Contenido del archivo en UTF-8, o string vacío si no existe.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.utils import read_text

file_path = Path("/ruta/archivo.txt")
content = read_text(file_path)
if content:
    print(content)
```

---

### `append_to_jornada_auto_section(path: Path, content: str) -> None`

Agrega contenido a la sección automática (3) de la bitácora de jornada.

**Parámetros**:
- `path` (Path): Ruta del archivo de bitácora (`YYYY-MM-DD.md`).
- `content` (str): Contenido a agregar.

**Comportamiento**:
1. Si el archivo no existe, crea la estructura inicial con `jornada_template()`.
2. Si existe, busca el separador `---\n\n## 3. Registro automático (NO EDITAR)`.
3. Agrega el contenido al final del archivo (append-only).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.utils import append_to_jornada_auto_section

bitacora_path = Path("/ruta/data/bitacora/2026-01-18.md")
content = "### Sesión S01\n- start: 2026-01-18T10:00:00-03:00\n"
append_to_jornada_auto_section(bitacora_path, content)
```

---

### `compute_content_hash(content: str) -> str`

Calcula hash SHA256 del contenido para detectar errores repetidos.

**Parámetros**:
- `content` (str): Contenido a hashear.

**Retorna**: `str` — Hash SHA256 en hexadecimal (64 caracteres).

**Ejemplo**:
```python
from dia_cli.utils import compute_content_hash

content = "Error: connection timeout"
hash_val = compute_content_hash(content)
# Retorna: "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
```

**Uso**: Se usa en `dia cap` para detectar si un error ya fue capturado previamente (mismo hash = error repetido).

---

### `find_last_unfixed_capture(events_path: Path, session_id: Optional[str] = None, day_id: Optional[str] = None) -> Optional[dict[str, Any]]`

Busca el último `CaptureCreated` sin `FixLinked` asociado.

**Parámetros**:
- `events_path` (Path): Ruta del archivo `events.ndjson`.
- `session_id` (Optional[str]): Si se especifica, busca solo en esa sesión.
- `day_id` (Optional[str]): Si se especifica, busca solo en ese día.

**Retorna**: `Optional[dict[str, Any]]` — Evento `CaptureCreated` sin fix, o `None` si no hay.

**Comportamiento**:
1. Lee todos los eventos del archivo.
2. Filtra por día y sesión si se especifican.
3. Recopila todos los `CaptureCreated` con sus hashes.
4. Recopila todos los `FixLinked` para saber cuáles están resueltos.
5. Encuentra el último `CaptureCreated` sin fix asociado.
6. Retorna el más reciente (ordenado por timestamp).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.utils import find_last_unfixed_capture

events_path = Path("/ruta/data/index/events.ndjson")

# Último error sin fix de cualquier sesión
error = find_last_unfixed_capture(events_path)

# Último error sin fix de una sesión específica
error = find_last_unfixed_capture(events_path, session_id="S01")

# Último error sin fix de un día específico
error = find_last_unfixed_capture(events_path, day_id="2026-01-18")
```

---

## Dependencias

- **Módulo estándar**: `datetime` (para timestamps)
- **Módulo estándar**: `hashlib` (para SHA256)
- **Módulo estándar**: `json` (para leer NDJSON)
- **Módulo estándar**: `pathlib` (para rutas)
- **Módulo estándar**: `typing` (para type hints)
- **Módulo interno**: `templates.jornada_template` (para crear bitácora inicial)

---

## Notas de Implementación

- `read_json_lines` es un generador: lee línea por línea sin cargar todo en memoria (útil para archivos grandes).
- `append_to_jornada_auto_section` mantiene la estructura de la bitácora (secciones manuales vs automáticas).
- `compute_content_hash` usa SHA256 para detectar errores idénticos (no similares, solo idénticos).
- `find_last_unfixed_capture` lee todo el archivo en memoria (puede ser lento con muchos eventos, pero suficiente para v0.1).

---

## Referencias

- [Guía de `dia cap`](../../guides/dia-cap.md)
- [Guía de `dia fix`](../../guides/dia-fix.md)
- [Módulo `ndjson`](ndjson.md)
- [Documentación de módulos CLI](README.md)
