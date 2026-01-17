Está pensado como **síntesis operativa**, no como documento largo: sirve para re-leer rápido, alinear criterio y no desviarse.

---

```md
# /dia — Resumen de diseño y workflow

## Decisión central
**A es la decisión correcta.**

`/dia` es un **repo único de registro**, no un core de código.  
Funciona como **caja negra + auditor** del trabajo diario, sin volverse un monstruo.

---

## Qué es /dia

`/dia`:
- observa repos externos (sin editarlos como core)
- impone rituales (sesión, commits, cierre)
- deja evidencia (eventos, diffs, métricas)
- alimenta al mentor (con límites claros)

NO es:
- un producto
- un framework
- un repositorio que contenga proyectos

SÍ es:
- bitácora inmutable
- auditor técnico
- disciplinador suave del workflow
- fuente de análisis posterior (mentor, grafos, patrones)

---

## Contrato de /dia con el mundo

`/dia` **no edita proyectos**: los audita y los disciplina.

### Tres funciones principales

1. **Registro**
   - bitácora por sesión
   - eventos inmutables

2. **Auditoría**
   - estado del repo al inicio y al final
   - diff y tamaño de cambios
   - detección de archivos “basura”

3. **Cierre útil**
   - resumen del día
   - tareas concretas de limpieza
   - recomendaciones de commits y docs

---

## Ritmo y guardrails (no moral)

### Regla práctica
- `/dia` no prohíbe
- `/dia` **avisa, registra y trae al cierre**

Ejemplo de evento automático:
- `CommitOverdue`: pasan >180 min sin commits durante una sesión IT

Esto **no bloquea**, pero queda registrado y aparece en el cierre.

---

## Comandos base (v0.1)

### `dia start --project <nombre> --repo <path>`
Crea sesión y captura baseline del repo:

- `git status --porcelain`
- `git rev-parse HEAD`
- `git diff` (si ya estaba sucio)
- rama actual
- recuento de cambios
- (opcional) archivos tocados recientemente

Se guarda en:
- `bitacora/YYYY-MM-DD/S01.md`
- `index/sessions.ndjson`
- `artifacts/S01_repo_baseline.txt`

---

### `dia end`
Captura estado final y compara contra baseline:

- commit final (`HEAD`)
- diff de la sesión:  
  `git diff <start_sha>..<end_sha> --stat`
- detección de:
  - `docs/scratch/**`
  - `*_test.py` fuera de `tests/`
  - commits gigantes (+X LOC)
- listado de commits:
  - `git log --oneline <start_sha>..HEAD`
  - (opcional) `--numstat`

Genera automáticamente:
- **CIERRE_Sxx.md** (análisis humano)
- **LIMPIEZA_Sxx.md** (acciones concretas)
- checklist “antes del próximo deploy”

---

## Archivos generados al cierre

### A) `CIERRE_Sxx.md`
- qué cambió realmente
- qué rompió el orden
- qué quedó riesgoso
- próxima acción clara

### B) `LIMPIEZA_Sxx.md`
Lista accionable, por ejemplo:
- mover `docs/scratch/*.md` → `docs/_scratch/`
- consolidar `15_test.py` → `tests/test_<feature>.py`
- dividir commits grandes en 2–3 commits normados
- crear/actualizar `docs/spec/<tema>.md`

Regla: **no opiniones, solo tareas**.

---

## Convenciones de commits (parte del método)

### Prefijos permitidos
- `feat:` nueva capacidad
- `fix:` corrección
- `refactor:` reordenamiento sin cambiar comportamiento
- `docs:` documentación
- `test:` tests
- `chore:` mantenimiento
- `wip:` solo si hay limpieza planificada al cierre

### Formato
```

<tipo>: <verbo> <objeto> [#sesion Sxx]

```

Ejemplos:
- `fix: prevent rollback loop [#sesion S01]`
- `docs: add session audit checklist [#sesion S02]`
- `chore: move scratch docs to _scratch [#sesion S01]`

La referencia de sesión permite:
- buscar
- graficar
- resumir patrones

---

## Contribución a documentación (sin contaminar)

`/dia` no “crea más docs”.  
**Convierte ruido en estructura**.

- capturas rápidas → `docs/_scratch/`
- decisiones reales → `docs/spec/`
- `/dia` sugiere consolidaciones cuando detecta redundancia

Resultado:
- menos contradicción
- más cohesión

---

## Modelo mental correcto: /dia como caja negra

`/dia` es el **registrador de vuelo**:
- no maneja el avión
- no decide la ruta
- registra qué pasó, cuándo, por qué y qué se tocó

Esto habilita:
- análisis posterior (Chroma, grafos)
- mentor con memoria real
- auditoría sin contaminar proyectos

---

## Mentor heredado (con límites claros)

El mentor solo puede:
1. **Recordar** contexto
2. **Alertar** patrones repetidos
3. **Sugerir** el siguiente paso ya decidido

No puede:
- decidir cierres
- abrir frentes nuevos
- hablar después de la campana

Apagado:
- `dia mentor off`
- automático tras `dia end`

Evento registrado:
- `MentorDisabled`

---

## Chroma + grafos (cuándo sí)

Secuencia sana:
1. 2–4 semanas de bitácora consistente
2. export NDJSON de eventos
3. recién ahí: Chroma + consultas + visualizaciones

Antes de eso: **basura vectorizada**.

---

## CLI + GUI (orden correcto)

- CLI → ritual y captura (start / note / end)
- GUI → visión (pizarrón, métricas, patrones)

La GUI **no es requisito** para trabajar.

---

## Decisión fijada (para no desviarse)

> `/dia` es un **repo único de registro**.  
> No contiene proyectos.  
> No se convierte en core.

Esta decisión:
- evita ENSAMBLE 2.0
- escala a multi-vida
- alimenta mentor y grafos sin contaminar

---

## Autonomía en staging (criterio de diseño)

Se fija el criterio de **autonomía total en staging con impacto acotado**, gates obligatorios y evidencia completa.  
Ver especificación: `docs/SPEC_FORK_MIN_DIA.md`.

---

## Alcance inmediato v0.1

Incluye solo:
- `dia start`
- `dia note`
- `dia end`
- generación de `Sxx.md` y `LIMPIEZA_Sxx.md`

Todo lo demás queda fuera **hasta tener datos limpios**.