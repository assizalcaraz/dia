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
   - bitácora por jornada (archivo único por día)
   - secciones manuales (editables) + automáticas (append-only)
   - eventos inmutables

2. **Auditoría**
   - estado del repo al inicio y al final
   - diff y tamaño de cambios
   - detección de archivos “basura”

3. **Cierre útil**
   - resumen del día (generado automáticamente)
   - análisis comparativo vs objetivo
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

**Múltiples sesiones por día**: `/dia` permite N sesiones por día sin restricciones. Los IDs se generan secuencialmente: S01, S02, S03, etc.

**Sesiones después de cierre**: Si el día ya fue cerrado con `dia close-day`, se genera evento `SessionStartedAfterDayClosed` en lugar de `SessionStarted`, pero la sesión se permite normalmente.

Se guarda en:
- `bitacora/YYYY-MM-DD.md` (archivo único por jornada, sección automática)
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
- Actualización de bitácora de jornada (sección automática)
- **CIERRE_Sxx.md** (legacy, mantenido por compatibilidad)
- **LIMPIEZA_Sxx.md** (acciones concretas)
- checklist "antes del próximo deploy"

---

### `dia close-day`
Cierra la jornada (ritual humano):

- registra evento `DayClosed` en `events.ndjson`
- opcionalmente marca bitácora con cierre humano
- **NO genera resúmenes** (los resúmenes se generan con `dia summarize`)
- **NO bloquea nuevas sesiones**: se pueden iniciar sesiones después del cierre

Este comando es un ritual que marca "hasta mañana", no un generador de análisis ni un bloqueador de trabajo.

**Comportamiento**: Si se ejecuta `dia start` después de `dia close-day`, se genera evento `SessionStartedAfterDayClosed` para registrar que la sesión comenzó tras el cierre, pero la sesión se permite normalmente.

---

### `dia summarize`
Genera resúmenes regenerables (vistas derivadas):

- `--mode rolling`: resumen durante el día (puede ejecutarse múltiples veces)
- `--mode nightly`: resumen al final del día (típicamente por cron)
- `--scope day`: alcance del resumen (v0: solo día)

Comportamiento:
- lee eventos del día/ventana
- extrae objetivo de bitácora (sección manual)
- analiza eventos con heurísticas (BLOCKED/OFF_TRACK/ON_TRACK)
- calcula delta vs último resumen rolling
- genera artefactos versionados (`artifacts/summaries/YYYY-MM-DD/rolling_<ts>.md`)
- registra evento `RollingSummaryGenerated` o `DailySummaryGenerated`
- agrega entrada a índice `summaries.ndjson` (append-only)

**Regla central**: Eventos/bitácora = fuente append-only. Resúmenes = vistas derivadas regenerables.

---

## Archivos generados

### Bitácora de jornada (`bitacora/YYYY-MM-DD.md`)

Estructura:
- **Sección 1**: Intención del día (manual, editable)
- **Sección 2**: Notas humanas (manual, editable)
- **Sección 3**: Registro automático (append-only, NO EDITAR)

Regla dura: `/dia` solo puede escribir a partir de la sección 3.

**Nota**: Los resúmenes ya no se agregan a la bitácora. Se generan como artefactos separados.

### Resúmenes regenerables (`artifacts/summaries/YYYY-MM-DD/`)

Generados por `dia summarize`:
- `rolling_<timestamp>.md` y `.json`: resúmenes durante el día
- `nightly_<timestamp>.md` y `.json`: resúmenes al final del día

Cada resumen incluye:
- assessment (ON_TRACK/OFF_TRACK/BLOCKED)
- next_step (próxima acción concreta)
- blocker (si existe)
- risks (lista de riesgos)
- delta (cambios desde último resumen rolling)
- objective (extraído de bitácora)

**Regla**: Resúmenes son vistas derivadas regenerables. Pueden ejecutarse múltiples veces sin reescribir anteriores.

### Índice de resúmenes (`index/summaries.ndjson`)

Índice append-only de todos los resúmenes generados:
- múltiples resúmenes por día (rolling + nightly)
- cada línea = un resumen generado
- formato: evento completo con tipo `RollingSummaryGenerated` o `DailySummaryGenerated`

### Archivos legacy (mantenidos por compatibilidad)

- `CIERRE_Sxx.md`: análisis de sesión
- `LIMPIEZA_Sxx.md`: tareas concretas de limpieza

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

## Alcance v0.1 (actualizado)

Incluye:
- `dia start` (inicia sesión, crea bitácora de jornada)
- `dia pre-feat` (sugiere commit)
- `dia end` (cierra sesión, actualiza bitácora)
- `dia close-day` (cierra jornada, ritual humano)
- `dia summarize` (genera resúmenes regenerables rolling/nightly)
- generación de bitácora única por jornada
- resúmenes regenerables como vistas derivadas
- separación clara: fuente (eventos) vs vistas (resúmenes)

Principio rector: **Los eventos son materia prima (append-only). Los resúmenes son vistas derivadas regenerables.**