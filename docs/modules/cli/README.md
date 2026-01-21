# Documentación de Módulos CLI

**Versión**: v0.1  
**Ubicación**: `cli/dia_cli/`

Este directorio contiene la documentación técnica de los módulos del CLI de `/dia`.

---

## Módulos

### Módulos Principales

- **[`git_ops.py`](git_ops.md)** — Operaciones Git (SHA, branch, status, diff, log, changed files)
- **[`sessions.py`](sessions.md)** — Gestión de sesiones (IDs, sesión activa)
- **[`config.py`](config.py)** — Configuración de rutas y directorios

### Módulos de Utilidad

- **[`templates.py`](templates.md)** — Plantillas Markdown para bitácoras y reportes
- **[`ndjson.py`](ndjson.md)** — Utilidad para escribir eventos en formato NDJSON
- **[`utils.py`](utils.md)** — Utilidades generales (timestamps, lectura de archivos, hashes)
- **[`rules.py`](rules.md)** — Carga de reglas y configuración
- **[`cursor_reminder.py`](cursor_reminder.md)** — Generación de recordatorios para Cursor

### Módulo Principal

- **`main.py`** — Lógica principal de comandos CLI (ver [Guías de comandos](../../guides/))

---

## Estructura de Módulos

```
cli/dia_cli/
├── __init__.py
├── main.py              # Comandos CLI principales
├── git_ops.py           # Operaciones Git
├── sessions.py          # Gestión de sesiones
├── config.py            # Configuración de rutas
├── templates.py         # Plantillas Markdown
├── ndjson.py            # Utilidad NDJSON
├── utils.py             # Utilidades generales
├── rules.py             # Carga de reglas
└── cursor_reminder.py   # Recordatorios Cursor
```

---

## Dependencias entre Módulos

```
main.py
├── git_ops.py
├── sessions.py
├── config.py
├── templates.py
├── ndjson.py
├── utils.py
├── rules.py
└── cursor_reminder.py
```

**Nota**: `main.py` importa y usa todos los demás módulos. Los módulos de utilidad son independientes entre sí.

---

## Referencias

- [Guías de comandos CLI](../../guides/)
- [Documentación de API](../api/endpoints.md)
- [Estructura NDJSON de eventos](../../specs/NDJSON.md)
