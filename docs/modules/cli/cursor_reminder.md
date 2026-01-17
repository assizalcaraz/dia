# Módulo: `cursor_reminder.py`

**Ubicación**: `cli/dia_cli/cursor_reminder.py`  
**Propósito**: Generación de recordatorios de workflow para Cursor IDE.

---

## Funciones Públicas

### `get_reminder() -> str`

Retorna el recordatorio de workflow como string.

**Retorna**: `str` — Contenido del recordatorio en Markdown.

**Contenido del recordatorio**:
```markdown
# Recordatorio: Workflow /dia para Cursor

## Commits de Cursor/IA

SIEMPRE usar cuando hagas commits:
```bash
git-commit-cursor -m "🦾 tipo: mensaje"
```

**Formato del mensaje**:
- 🦾 al INICIO (identificación rápida en git log)
- NO incluir `[dia]` (confunde)
- Ejemplo: `🦾 feat: agregar validación de datos [#sesion S01]`

**Autoría automática**: `Cursor Assistant <cursor@dia.local>`

## Commits manuales del usuario

El usuario usa: `git -M "mensaje"` (sin emoji, su autoría normal)

## Identificación en git log

- `Cursor Assistant <cursor@dia.local>` + 🦾 = commit de Cursor
- Autoría del usuario + sin 🦾 = commit manual

## Workflow /dia

- `dia start`: inicia sesión
- `dia pre-feat`: sugiere commit (usa `git-commit-cursor`)
- `dia end`: cierra sesión

NO ejecutar commits automáticamente, solo sugerir.
```

**Ejemplo**:
```python
from dia_cli.cursor_reminder import get_reminder

reminder = get_reminder()
print(reminder)
```

---

### `write_reminder_to_file(path: Path) -> None`

Escribe el recordatorio a un archivo (típicamente `.cursorrules`).

**Parámetros**:
- `path` (Path): Ruta del archivo donde escribir (ej: `.cursorrules` en el repo).

**Comportamiento**:
- Crea el directorio padre si no existe.
- Escribe el contenido del recordatorio en UTF-8.
- Sobrescribe el archivo si existe.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.cursor_reminder import write_reminder_to_file

reminder_path = Path("/ruta/al/repo/.cursorrules")
write_reminder_to_file(reminder_path)
```

---

## Uso en CLI

El comando `dia start` usa este módulo para generar `.cursorrules` automáticamente:

```python
from dia_cli.cursor_reminder import write_reminder_to_file

# En cmd_start()
reminder_path = repo_path / ".cursorrules"
write_reminder_to_file(reminder_path)
```

**Resultado**: Cada vez que ejecutas `dia start`, se regenera `.cursorrules` en el repositorio activo.

---

## Uso Manual

También puedes generar el recordatorio manualmente:

```bash
python3 -m dia_cli.cursor_reminder > .cursorrules
```

O desde Python:

```python
from pathlib import Path
from dia_cli.cursor_reminder import write_reminder_to_file

write_reminder_to_file(Path(".cursorrules"))
```

---

## Contenido del Recordatorio

El recordatorio documenta:

1. **Convención de commits de Cursor/IA**:
   - Usar `git-commit-cursor`
   - Formato: `🦾 tipo: mensaje`
   - Autoría: `Cursor Assistant <cursor@dia.local>`

2. **Convención de commits manuales**:
   - Usar `git -M`
   - Sin emoji
   - Autoría normal del usuario

3. **Workflow /dia**:
   - Comandos principales
   - No ejecutar commits automáticamente

---

## Dependencias

- **Módulo estándar**: `pathlib` (para rutas)

---

## Notas de Implementación

- El recordatorio es un string constante `REMINDER` definido en el módulo.
- Se regenera cada vez que ejecutas `dia start` (no se verifica si ya existe).
- El formato es Markdown simple para que Cursor lo lea fácilmente.

---

## Referencias

- [Guía de `dia start`](../../guides/dia-start.md)
- [Convención de commits](../../overview/RESUMEN_DISENO_DIA.md#convenciones-de-commits)
- [Documentación de módulos CLI](README.md)
