# Módulo: `config.py`

**Ubicación**: `cli/dia_cli/config.py`  
**Propósito**: Configuración de rutas y directorios del sistema de datos.

---

## Funciones Públicas

### `repo_root() -> Path`

Obtiene la ruta raíz del repositorio `/dia`.

**Retorna**: `Path` — Ruta absoluta del directorio raíz del proyecto.

**Comportamiento**: Calcula la ruta relativa desde `config.py` (sube 2 niveles: `cli/dia_cli/` → `cli/` → raíz).

**Ejemplo**:
```python
from dia_cli.config import repo_root

root = repo_root()
# Retorna: /Users/joseassizalcarazbaxter/Developer/dia
```

---

### `data_root(override: Optional[str] = None) -> Path`

Obtiene la ruta base del directorio `data/`.

**Parámetros**:
- `override` (Optional[str]): Ruta personalizada. Si se especifica, se usa esta en lugar del default.

**Retorna**: `Path` — Ruta absoluta del directorio `data/`.

**Comportamiento**:
- Si `override` se especifica, expande y resuelve esa ruta.
- Si `override` es `None`, retorna `repo_root() / "data"`.

**Ejemplo**:
```python
from dia_cli.config import data_root

# Default: repo_root/data
default_data = data_root()

# Personalizado
custom_data = data_root("/ruta/personalizada/data")
```

---

### `index_dir(root: Path) -> Path`

Obtiene la ruta del directorio de índices.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del directorio `index/` (contiene `events.ndjson`, `sessions.ndjson`, etc.).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, index_dir

root = data_root()
index = index_dir(root)
# Retorna: root / "index"
```

---

### `bitacora_dir(root: Path) -> Path`

Obtiene la ruta del directorio de bitácoras.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del directorio `bitacora/` (contiene bitácoras de jornada).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, bitacora_dir

root = data_root()
bitacora = bitacora_dir(root)
# Retorna: root / "bitacora"
```

---

### `artifacts_dir(root: Path) -> Path`

Obtiene la ruta del directorio de artefactos.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del directorio `artifacts/` (contiene diffs, logs, capturas).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, artifacts_dir

root = data_root()
artifacts = artifacts_dir(root)
# Retorna: root / "artifacts"
```

---

### `captures_dir(root: Path) -> Path`

Obtiene la ruta del directorio de capturas.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del directorio `artifacts/captures/` (contiene errores/logs capturados).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, captures_dir

root = data_root()
captures = captures_dir(root)
# Retorna: root / "artifacts" / "captures"
```

---

### `rules_path(root: Path) -> Path`

Obtiene la ruta del archivo de reglas.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del archivo `rules.json`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, rules_path

root = data_root()
rules = rules_path(root)
# Retorna: root / "rules.json"
```

---

### `analysis_dir(root: Path) -> Path`

Obtiene la ruta del directorio de análisis.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Retorna**: `Path` — Ruta del directorio `analysis/` (contiene análisis vs objetivo).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, analysis_dir

root = data_root()
analysis = analysis_dir(root)
# Retorna: root / "analysis"
```

---

### `ensure_data_dirs(root: Path) -> None`

Crea la estructura de directorios necesaria si no existe.

**Parámetros**:
- `root` (Path): Ruta base del directorio `data/`.

**Comportamiento**: Crea los siguientes directorios si no existen:
- `index/`
- `bitacora/`
- `artifacts/`
- `artifacts/captures/`
- `analysis/`

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.config import data_root, ensure_data_dirs

root = data_root()
ensure_data_dirs(root)
# Crea todos los directorios necesarios
```

---

## Estructura de Directorios

```
data/
├── index/
│   ├── events.ndjson
│   ├── sessions.ndjson
│   └── daily_summaries.ndjson
├── bitacora/
│   └── YYYY-MM-DD.md
├── artifacts/
│   ├── S01_repo_diff_start.patch
│   └── captures/
│       └── YYYY-MM-DD/
│           └── S01/
│               ├── cap_<id>.txt
│               └── cap_<id>.meta.json
├── analysis/
│   └── YYYY-MM-DD_vs_objetivo.md
└── rules.json
```

---

## Dependencias

- **Módulo estándar**: `pathlib` (para rutas)

---

## Notas de Implementación

- Todas las funciones retornan `Path` objetos (no strings) para facilitar manipulación de rutas.
- Las rutas se resuelven como absolutas usando `.resolve()`.
- `ensure_data_dirs` usa `mkdir(parents=True, exist_ok=True)` para crear directorios de forma segura.

---

## Referencias

- [Guía de `dia start`](../../guides/dia-start.md)
- [Documentación de módulos CLI](README.md)
