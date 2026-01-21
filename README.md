# /dia — v0.1

Herramienta de hábito y cierre. Registra sesiones de trabajo en formato NDJSON y genera bitácoras inmutables.

El foco de v0.1 es instalar el ciclo: iniciar → trabajar → cerrar.

---

## Qué es /dia

`/dia` es un sistema de registro y auditoría para sesiones de trabajo:

- **CLI local**: Inicia, checkpoint y cierre de sesión
- **UI web (Svelte)**: Zona indeleble (bitácoras, resúmenes, docs) y zona viva (sesión activa, objetivos)
- **API Django read-only**: Expone sesiones y eventos
- **Rutinas técnicas declarativas**: Sugieren y registran, no ejecutan

## Qué no es

- No ejecuta commits ni pushes
- No toca ramas protegidas
- No es agente autónomo (v0.1)

---

## Instalación Rápida

### Requisitos

- Python 3.9+ con venv local `envdia`
- Docker para `server` + `ui`
- Repo Git local donde se trabaja la sesión

### CLI (local)

```bash
source envdia/bin/activate
cd cli
pip install -e .
```

Si aparece `No module named pip`:
```bash
python3 -m pip install --upgrade pip setuptools wheel
```

### UI + API (Docker)

```bash
make up
```

- UI: `http://localhost:5173`
- API: `http://localhost:8000/api`

---

## Uso Rápido

Desde el repo donde vas a trabajar:

```bash
cd /ruta/al/repo
dia start --data-root /ruta/al/monorepo/data --area it
```

**Workflow básico**:
```bash
# Capturar error
comando_que_falla 2>&1 | dia cap --kind error --title "descripción" --data-root /ruta/data --area it

# Linkear fix
dia fix --title "descripción del fix" --data-root /ruta/data --area it

# Checkpoint y cierre
dia pre-feat --data-root /ruta/data --area it
dia end --data-root /ruta/data --area it
dia close-day --data-root /ruta/data --area it
```

---

## Gestión de Datos

El directorio `/data` contiene datos de uso (runtime data) y está **excluido del repositorio** para:
- Separar datos de uso de documentos de desarrollo
- Evitar commits accidentales de información sensible
- Permitir uso multi-proyecto sin mezclar datos

**Estrategia Opción B2 (híbrido)**:
1. `--data-root` explícito (soberanía)
2. `.dia/` local en el repo (datos por proyecto)
3. Data global según OS (fallback automático)

📖 Ver guía completa: [Gestión de Datos](docs/guides/gestion-data.md)

---

## Estructura del Proyecto

```
/dia
├── cli/              # CLI Python (dia start, dia end, etc.)
├── server/           # Django API read-only
├── ui/               # UI Svelte (zona indeleble + zona viva)
├── docs/             # Documentación completa
└── data/             # Datos de uso (excluido del repo)
```

**Nota**: El directorio `data/` está excluido del repositorio. Ver [Gestión de Datos](docs/guides/gestion-data.md).

---

## Documentación Completa

### Nivel 1: Entendimiento General

Documentación para entender qué es `/dia`, su filosofía y cómo empezar.

- **[Resumen de diseño](docs/overview/RESUMEN_DISENO_DIA.md)** — Síntesis operativa del diseño y workflow
- **[Estado actual](docs/overview/ESTADO_ACTUAL.md)** — Estado técnico del proyecto
- **[Tutorial completo](docs/manual/TUTORIAL_INTRO_V0_1.md)** — Guía paso a paso para usuarios

### Nivel 2: Especificaciones Técnicas

Documentación técnica de formatos, estructuras y especificaciones.

- **[Estructura NDJSON de eventos](docs/dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))** — Formato de eventos y catálogo completo
- **[SPEC fork mínimo](docs/specs/SPEC_FORK_MIN_DIA.md)** — Especificación de autonomía en staging (futuro)

### Nivel 3: Documentación de Módulos

Documentación técnica de módulos y componentes del sistema.

#### CLI

- **[Índice de módulos CLI](docs/modules/cli/README.md)**
  - [`git_ops.py`](docs/modules/cli/git_ops.md) — Operaciones Git
  - [`sessions.py`](docs/modules/cli/sessions.md) — Gestión de sesiones
  - [`config.py`](docs/modules/cli/config.md) — Configuración de rutas
  - [`templates.py`](docs/modules/cli/templates.md) — Plantillas Markdown
  - [`ndjson.py`](docs/modules/cli/ndjson.md) — Utilidad NDJSON
  - [`utils.py`](docs/modules/cli/utils.md) — Utilidades generales
  - [`rules.py`](docs/modules/cli/rules.md) — Carga de reglas
  - [`cursor_reminder.py`](docs/modules/cli/cursor_reminder.md) — Recordatorios Cursor

#### API

- **[Endpoints API](docs/modules/api/endpoints.md)** — Documentación completa de endpoints Django

#### UI

- **[Componente principal](docs/ui/App.md)** — `App.svelte` (zona indeleble + zona viva)
- **[Índice de componentes UI](docs/ui/components/README.md)**
  - [`BitacoraViewer`](docs/ui/components/BitacoraViewer.md) — Visualizador de bitácoras
  - [`BitacoraEditor`](docs/ui/components/BitacoraEditor.md) — Editor de bitácoras
  - [`SummariesViewer`](docs/ui/components/SummariesViewer.md) — Visualizador de resúmenes
  - [`DocsViewer`](docs/ui/components/DocsViewer.md) — Visualizador de documentación
  - [`SessionObjectives`](docs/ui/components/SessionObjectives.md) — Objetivos de sesión
  - [`ErrorFixCommitChain`](docs/ui/components/ErrorFixCommitChain.md) — Cadena Error→Fix→Commit
  - [`TemporalNotesViewer`](docs/ui/components/TemporalNotesViewer.md) — Notas temporales
  - [`BoardView`](docs/ui/BoardView.md) — Feature Board fullscreen (v0.2)

### Nivel 4: Guías de Herramientas

Guías específicas de cada comando y herramienta.

- **[`dia start`](docs/guides/dia-start.md)** — Iniciar sesión
- **[`dia pre-feat`](docs/guides/dia-pre-feat.md)** — Checkpoint pre-feat
- **[`dia end`](docs/guides/dia-end.md)** — Cerrar sesión
- **[`dia close-day`](docs/guides/dia-close-day.md)** — Cerrar jornada
- **[`dia summarize`](docs/guides/dia-summarize.md)** — Generar resúmenes
- **[`dia cap`](docs/guides/dia-cap.md)** — Capturar errores/logs
- **[`dia fix`](docs/guides/dia-fix.md)** — Linkear fix a error
- **[Workflow Error→Fix→Commit](docs/guides/workflow_error_fix_commit.md)** — Guía completa del workflow
- **[Sesiones múltiples](docs/guides/sesiones-multiples.md)** — Múltiples sesiones por día
- **[Usar dia durante desarrollo](docs/guides/dia-desarrollo.md)** — Guía práctica para desarrolladores
- **[Gestión de datos](docs/guides/gestion-data.md)** — Estrategia de gestión de `/data`
- **[Scopes de documentación](docs/guides/documentacion-scopes.md)** — Actualizar documentación según cambios

---

## Rutas de Aprendizaje

### Para Usuarios Nuevos

1. **[Resumen de diseño](docs/overview/RESUMEN_DISENO_DIA.md)** — Entender qué es `/dia`
2. **[Tutorial completo](docs/manual/TUTORIAL_INTRO_V0_1.md)** — Aprender a usar
3. **[Guías de comandos](docs/guides/)** — Referencia rápida por comando

### Para Desarrolladores

1. **[Resumen de diseño](docs/overview/RESUMEN_DISENO_DIA.md)** — Entender arquitectura
2. **[Documentación de módulos CLI](docs/modules/cli/README.md)** — Entender código
3. **[Documentación de componentes UI](docs/ui/components/README.md)** — Entender componentes
4. **[Documentación de API](docs/modules/api/endpoints.md)** — Entender endpoints
5. **[Estructura NDJSON](docs/dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))** — Entender formato de datos

### Para Contribuidores

1. **[Estado actual](docs/overview/ESTADO_ACTUAL.md)** — Ver qué está implementado
2. **[Documentación de módulos](docs/modules/)** — Entender estructura del código
3. **[Especificaciones](docs/specs/)** — Ver qué falta implementar
4. **[Scopes de documentación](docs/guides/documentacion-scopes.md)** — Cómo actualizar documentación

---

## Referencias Rápidas

- **Inicio rápido**: Este README
- **Instalación**: [Tutorial completo](docs/manual/TUTORIAL_INTRO_V0_1.md)
- **Comandos CLI**: [Guías de comandos](docs/guides/)
- **API**: [Endpoints](docs/modules/api/endpoints.md)
- **Formato de eventos**: [NDJSON](docs/dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))
- **Gestión de datos**: [Guía de gestión de datos](docs/guides/gestion-data.md)

---

## Convención de Commits

**Sistema de identificación**:
- **Commits de Cursor/IA**: `git-commit-cursor` → autoría `Cursor Assistant <cursor@dia.local>` + 🦾 al INICIO
- **Commits manuales**: `git -M` → tu autoría normal, sin emoji

**Formato**: `🦾 tipo: mensaje [#sesion Sxx]` (sin `[dia]`)

**Recordatorios automáticos**: `dia start` genera `.cursorrules` en el repo activo para que Cursor recuerde el workflow.

---

## Datos Generados

Los datos se almacenan según la estrategia Opción B2 (ver [Gestión de Datos](docs/guides/gestion-data.md)). Estructura típica:

- `index/events.ndjson` (append-only)
- `index/summaries.ndjson` (append-only, resúmenes rolling/nightly)
- `bitacora/YYYY-MM-DD.md` (archivo único por jornada, secciones manuales + automáticas)
- `artifacts/summaries/YYYY-MM-DD/` (resúmenes regenerables)
- `artifacts/captures/YYYY-MM-DD/Sxx/` (errores/logs capturados)

---

## Sesiones Múltiples

`/dia` permite **N sesiones por día** sin restricciones. Cada sesión se identifica con ID secuencial (S01, S02, S03, etc.).

- `dia close-day` marca el día como cerrado pero **no bloquea nuevas sesiones**
- Sesiones iniciadas después del cierre generan evento `SessionStartedAfterDayClosed`

📖 Ver [Sesiones múltiples](docs/guides/sesiones-multiples.md) para más detalles

---

**Última actualización**: 2026-01-19
