# Módulo: `templates.py`

**Ubicación**: `cli/dia_cli/templates.py`  
**Propósito**: Plantillas Markdown para generar bitácoras, reportes y análisis.

---

## Funciones Públicas

### `jornada_template(day_id: str) -> str`

Genera la plantilla inicial para bitácora de jornada (archivo único por día).

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD` (ej: `"2026-01-18"`).

**Retorna**: `str` — Contenido Markdown de la plantilla inicial.

**Estructura generada**:
```markdown
# Jornada YYYY-MM-DD

## 1. Intención del día (manual)
- Objetivo principal:
- Definición de Hecho (DoD):
- Restricciones / contexto:

## 2. Notas humanas (manual)
- ideas
- dudas
- decisiones
- observaciones subjetivas relevantes

---

## 3. Registro automático (NO EDITAR)
(append-only, escrito por /dia)
```

**Ejemplo**:
```python
from dia_cli.templates import jornada_template

template = jornada_template("2026-01-18")
# Retorna plantilla con secciones 1, 2 y inicio de 3
```

---

### `session_start_template(...) -> str`

**⚠️ LEGACY**: Esta función está marcada como legacy y ya no se usa. Se mantiene por compatibilidad.

Genera plantilla de bitácora de sesión individual (formato antiguo).

**Parámetros**:
- `day_id` (str): Fecha.
- `session_id` (str): ID de sesión.
- `intent` (str): Intención.
- `dod` (str): Definición de Hecho.
- `mode` (str): Modo.
- `repo_path` (str): Ruta del repo.
- `branch` (str): Rama.
- `start_sha` (str): SHA inicial.

**Retorna**: `str` — Plantilla legacy (no se usa en v0.1).

---

### `session_auto_section_template(...) -> str`

Genera la sección automática de sesión para agregar a bitácora de jornada.

**Parámetros**:
- `session_id` (str): ID de sesión (ej: `"S01"`).
- `start_ts` (str): Timestamp ISO 8601 de inicio.
- `intent` (str): Intención de la sesión.
- `dod` (str): Definición de Hecho.
- `mode` (str): Modo de la sesión.
- `repo_path` (str): Ruta del repositorio.
- `branch` (str): Rama actual.
- `start_sha` (str): SHA inicial (o `"None"` si no hay commits).

**Retorna**: `str` — Contenido Markdown de la sección de sesión.

**Estructura generada**:
```markdown
### Sesión S01
- start: 2026-01-18T10:00:00-03:00
- intent: Implementar feature X
- dod: Feature funcionando y tests pasando
- mode: it
- repo: /ruta/al/repo
- branch: main
- start_sha: abc123
- end: (pendiente)
- commits: (pendiente)
- eventos:

#### Eventos
```

**Ejemplo**:
```python
from dia_cli.templates import session_auto_section_template

section = session_auto_section_template(
    session_id="S01",
    start_ts="2026-01-18T10:00:00-03:00",
    intent="Implementar feature X",
    dod="Feature funcionando",
    mode="it",
    repo_path="/ruta/al/repo",
    branch="main",
    start_sha="abc123"
)
```

---

### `cierre_template(day_id: str, session_id: str, summary: str, warnings: Iterable[str], next_action: str) -> str`

Genera plantilla de cierre de sesión (archivo legacy `CIERRE_Sxx.md`).

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD`.
- `session_id` (str): ID de sesión.
- `summary` (str): Resumen de la sesión.
- `warnings` (Iterable[str]): Lista de alertas.
- `next_action` (str): Próxima acción sugerida.

**Retorna**: `str` — Contenido Markdown del cierre.

**Estructura generada**:
```markdown
# CIERRE 2026-01-18 S01

## Resumen

3 commits, 12 archivos tocados.

## Alertas

- Sin alertas

## Proxima accion

- Revisar limpieza
```

**Ejemplo**:
```python
from dia_cli.templates import cierre_template

cierre = cierre_template(
    day_id="2026-01-18",
    session_id="S01",
    summary="3 commits, 12 archivos tocados.",
    warnings=[],
    next_action="Revisar limpieza"
)
```

---

### `limpieza_template(day_id: str, session_id: str, tasks: Iterable[str]) -> str`

Genera plantilla de tareas de limpieza (archivo legacy `LIMPIEZA_Sxx.md`).

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD`.
- `session_id` (str): ID de sesión.
- `tasks` (Iterable[str]): Lista de tareas de limpieza.

**Retorna**: `str` — Contenido Markdown de limpieza.

**Estructura generada**:
```markdown
# LIMPIEZA 2026-01-18 S01

## Tareas

- Mover docs/scratch/notas.md -> docs/_scratch/ (evitar drift)
- Mover 15_test.py a tests/test_<feature>.py
```

**Ejemplo**:
```python
from dia_cli.templates import limpieza_template

tasks = [
    "Mover docs/scratch/notas.md -> docs/_scratch/",
    "Mover 15_test.py a tests/"
]
limpieza = limpieza_template(
    day_id="2026-01-18",
    session_id="S01",
    tasks=tasks
)
```

---

### `daily_summary_template(...) -> str`

Genera plantilla para resumen del día (sección 5 de bitácora).

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD`.
- `objective` (str): Objetivo principal del día.
- `attempted` (str): Qué se intentó.
- `achieved` (str): Qué se logró realmente.
- `not_achieved` (str): Qué no se logró y por qué.
- `deviations` (Iterable[str]): Lista de desvíos detectados.

**Retorna**: `str` — Contenido Markdown del resumen.

**Estructura generada**:
```markdown
## 5. Resumen del día (generado)

- Qué se intentó: 2 sesiones iniciadas
- Qué se logró realmente: 2 sesiones cerradas, 15 eventos registrados
- Qué no se logró y por qué: Todas las sesiones cerradas
- Desvíos detectados:
- Sin desvíos detectados
```

**Ejemplo**:
```python
from dia_cli.templates import daily_summary_template

summary = daily_summary_template(
    day_id="2026-01-18",
    objective="Implementar autenticación OAuth2",
    attempted="2 sesiones iniciadas",
    achieved="2 sesiones cerradas, 15 eventos registrados",
    not_achieved="Todas las sesiones cerradas",
    deviations=[]
)
```

---

### `analysis_vs_objective_template(...) -> str`

Genera plantilla para análisis comparativo vs objetivo.

**Parámetros**:
- `day_id` (str): Fecha en formato `YYYY-MM-DD`.
- `objective` (str): Objetivo declarado.
- `expected_plan` (str): Plan esperado (DoD).
- `actual_result` (str): Resultado real.
- `gaps` (Iterable[str]): Lista de brechas detectadas.
- `impact` (str): Impacto del resultado.
- `suggested_adjustments` (Iterable[str]): Lista de ajustes sugeridos.

**Retorna**: `str` — Contenido Markdown del análisis.

**Estructura generada**:
```markdown
# Análisis 2026-01-18 vs Objetivo

## Objetivo declarado
Implementar autenticación OAuth2

## Plan esperado
Login funcional, tests pasando, docs actualizados

## Resultado real
2 sesiones cerradas, 15 eventos registrados

## Brechas
- Sin brechas

## Impacto
2/2 sesiones completadas

## Ajustes sugeridos
- Sin ajustes sugeridos
```

**Ejemplo**:
```python
from dia_cli.templates import analysis_vs_objective_template

analysis = analysis_vs_objective_template(
    day_id="2026-01-18",
    objective="Implementar autenticación OAuth2",
    expected_plan="Login funcional, tests pasando",
    actual_result="2 sesiones cerradas, 15 eventos",
    gaps=[],
    impact="2/2 sesiones completadas",
    suggested_adjustments=[]
)
```

---

## Dependencias

- **Módulo estándar**: `typing` (para `Iterable`)

---

## Notas de Implementación

- Todas las plantillas retornan strings Markdown simples.
- Las plantillas legacy (`session_start_template`, `cierre_template`, `limpieza_template`) se mantienen por compatibilidad pero el formato principal es la bitácora de jornada.
- Las plantillas no validan el contenido, solo formatean.

---

## Referencias

- [Guía de `dia start`](../../guides/dia-start.md)
- [Guía de `dia end`](../../guides/dia-end.md)
- [Guía de `dia close-day`](../../guides/dia-close-day.md)
- [Documentación de módulos CLI](README.md)
