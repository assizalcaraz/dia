"""
Genera recordatorio de workflow para Cursor.
Se puede ejecutar automáticamente o incluir en contexto inicial.
"""
from pathlib import Path

REMINDER = """# Recordatorio: Workflow /dia para Cursor

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
"""


def get_reminder() -> str:
    """Retorna el recordatorio como string."""
    return REMINDER


def write_reminder_to_file(path: Path) -> None:
    """Escribe el recordatorio a un archivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(REMINDER, encoding="utf-8")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        write_reminder_to_file(Path(sys.argv[1]))
    else:
        print(REMINDER)
