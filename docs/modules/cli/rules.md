# Módulo: `rules.py`

**Ubicación**: `cli/dia_cli/rules.py`  
**Propósito**: Carga de reglas y configuración desde `rules.json`.

---

## Funciones Públicas

### `load_rules(path: Path) -> dict[str, Any]`

Carga reglas desde un archivo JSON o retorna defaults.

**Parámetros**:
- `path` (Path): Ruta del archivo `rules.json`.

**Retorna**: `dict[str, Any]` — Diccionario con reglas cargadas o defaults.

**Comportamiento**:
- Si el archivo existe, lo lee y parsea como JSON.
- Si el archivo no existe, retorna `DEFAULT_RULES`.

**Estructura de reglas**:
```python
{
    "protected_branches": ["main", "master", "production", "prod"],
    "commit_tag": "[dia]",
    "commit_types": ["feat", "fix", "refactor", "docs", "test", "chore", "wip"],
    "suspicious_patterns": [
        {"pattern": "docs/scratch/", "rule": "docs_scratch"},
        {"pattern": "_test.py", "rule": "test_outside_tests"}
    ]
}
```

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.rules import load_rules

rules_path = Path("/ruta/data/rules.json")
rules = load_rules(rules_path)

# Acceder a reglas
protected = rules["protected_branches"]
patterns = rules["suspicious_patterns"]
```

---

## Reglas por Defecto

Si `rules.json` no existe, se usan estas reglas:

```python
DEFAULT_RULES = {
    "protected_branches": ["main", "master", "production", "prod"],
    "commit_tag": "[dia]",
    "commit_types": ["feat", "fix", "refactor", "docs", "test", "chore", "wip"],
    "suspicious_patterns": [
        {"pattern": "docs/scratch/", "rule": "docs_scratch"},
        {"pattern": "_test.py", "rule": "test_outside_tests"}
    ]
}
```

**Campos**:
- `protected_branches`: Lista de ramas protegidas (no se usan en v0.1, reservado para futuro).
- `commit_tag`: Tag para commits (legacy, no se usa en v0.1).
- `commit_types`: Tipos de commit permitidos.
- `suspicious_patterns`: Patrones de archivos sospechosos para detección en `dia end`.

---

## Uso de Reglas

### Detección de Archivos Sospechosos

En `dia end`, se usan `suspicious_patterns` para detectar archivos que requieren limpieza:

```python
from dia_cli.rules import load_rules

rules = load_rules(rules_path)
patterns = rules["suspicious_patterns"]

for file_path in changed_files:
    for pattern_info in patterns:
        pattern = pattern_info["pattern"]
        rule = pattern_info["rule"]
        if pattern in file_path:
            # Archivo sospechoso detectado
            tasks.append(f"Mover {file_path} según regla {rule}")
```

**Patrones actuales**:
- `docs/scratch/`: Archivos en directorio scratch (sugerir mover a `docs/_scratch/`).
- `_test.py`: Tests fuera del directorio `tests/` (sugerir mover a `tests/`).

---

## Dependencias

- **Módulo estándar**: `json` (para leer JSON)
- **Módulo estándar**: `pathlib` (para rutas)
- **Módulo estándar**: `typing` (para type hints)

---

## Notas de Implementación

- El archivo `rules.json` es opcional. Si no existe, se usan defaults.
- Las reglas se cargan cada vez que se llama a `load_rules()` (no hay caché).
- Los defaults están definidos como constante `DEFAULT_RULES` en el módulo.

---

## Referencias

- [Guía de `dia end`](../../guides/dia-end.md)
- [Documentación de módulos CLI](README.md)
