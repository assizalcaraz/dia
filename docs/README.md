# Documentación de /dia

**Versión**: v0.1  
**Última actualización**: 2026-01-19

Este directorio contiene toda la documentación del proyecto `/dia`, organizada en niveles de lectura claros y siguiendo la estructura del proyecto.

---

## Niveles de Lectura

### Nivel 1: Entendimiento General

Documentación para entender qué es `/dia`, su filosofía y cómo empezar.

- **[Resumen de diseño](overview/RESUMEN_DISENO_DIA.md)** — Síntesis operativa del diseño y workflow
- **[Estado actual](overview/ESTADO_ACTUAL.md)** — Estado técnico del proyecto

**Para empezar**: Lee el [Resumen de diseño](overview/RESUMEN_DISENO_DIA.md) y luego el [Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md).

---

### Nivel 2: Especificaciones Técnicas

Documentación técnica de formatos, estructuras y especificaciones.

- **[Estructura NDJSON de eventos](../dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))** — Formato de eventos y catálogo completo
- **[SPEC fork mínimo](specs/SPEC_FORK_MIN_DIA.md)** — Especificación de autonomía en staging (futuro)

---

### Nivel 2: Documentación de Módulos

Documentación técnica de módulos y componentes del sistema.

#### CLI

- **[Índice de módulos CLI](modules/cli/README.md)**
  - [`git_ops.py`](modules/cli/git_ops.md) — Operaciones Git
  - [`sessions.py`](modules/cli/sessions.md) — Gestión de sesiones
  - [`config.py`](modules/cli/config.md) — Configuración de rutas
  - [`templates.py`](modules/cli/templates.md) — Plantillas Markdown
  - [`ndjson.py`](modules/cli/ndjson.md) — Utilidad NDJSON
  - [`utils.py`](modules/cli/utils.md) — Utilidades generales
  - [`rules.py`](modules/cli/rules.md) — Carga de reglas
  - [`cursor_reminder.py`](modules/cli/cursor_reminder.md) — Recordatorios Cursor

#### API

- **[Endpoints API](modules/api/endpoints.md)** — Documentación completa de endpoints Django

#### UI

- **[Componente principal](ui/App.md)** — `App.svelte` (zona indeleble + zona viva)
- **[Índice de componentes UI](ui/components/README.md)**
  - [`BitacoraViewer`](ui/components/BitacoraViewer.md) — Visualizador de bitácoras
  - [`BitacoraEditor`](ui/components/BitacoraEditor.md) — Editor de bitácoras
  - [`SummariesViewer`](ui/components/SummariesViewer.md) — Visualizador de resúmenes
  - [`DocsViewer`](ui/components/DocsViewer.md) — Visualizador de documentación
  - [`DocTreeNode`](ui/components/DocTreeNode.md) — Componente de árbol de documentación
  - [`MarkdownRenderer`](ui/components/MarkdownRenderer.md) — Renderizador de markdown
  - [`SessionObjectives`](ui/components/SessionObjectives.md) — Objetivos de sesión
  - [`ErrorFixCommitChain`](ui/components/ErrorFixCommitChain.md) — Cadena Error→Fix→Commit
  - [`TemporalNotesViewer`](ui/components/TemporalNotesViewer.md) — Notas temporales
  - [`BoardView`](ui/BoardView.md) — Feature Board fullscreen (v0.2)
  - [`BoardElement`](ui/components/BoardElement.md) — Elementos del board

---

### Nivel 3: Guías de Herramientas

Guías específicas de cada comando y herramienta.

- **[`dia start`](guides/dia-start.md)** — Iniciar sesión
- **[`dia pre-feat`](guides/dia-pre-feat.md)** — Checkpoint pre-feat
- **[`dia end`](guides/dia-end.md)** — Cerrar sesión
- **[`dia close-day`](guides/dia-close-day.md)** — Cerrar jornada
- **[`dia summarize`](guides/dia-summarize.md)** — Generar resúmenes
- **[`dia E`](guides/dia-desarrollo.md#capturar-errores)** — Capturar error con título automático (comando corto)
- **[`dia cap`](guides/dia-cap.md)** — Capturar errores/logs (comando completo)
- **[`dia fix`](guides/dia-fix.md)** — Linkear fix a error
- **[Workflow Error→Fix→Commit](guides/workflow_error_fix_commit.md)** — Guía completa del workflow
- **[Sesiones múltiples](guides/sesiones-multiples.md)** — Múltiples sesiones por día
- **[Tips: Usar dia durante desarrollo](guides/dia-desarrollo.md)** — Guía práctica para desarrolladores
- **[Gestión de datos](guides/gestion-data.md)** — Estrategia de gestión de `/data` (Opción B2)
- **[Scopes de Documentación](guides/documentacion-scopes.md)** — Guía para actualizar documentación según cambios

---

### Nivel 1: Tutorial de Usuario

Tutorial paso a paso para usuarios.

- **[Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md)** — Guía completa de uso
- **[Captura de errores](manual/CAPTURA_ERRORES.md)** — Guía específica de captura de errores

---

## Estructura del Directorio

La estructura de documentación refleja la estructura del proyecto:

```
docs/
├── README.md (este archivo)
├── overview/          # Nivel 1: Entendimiento general
│   ├── RESUMEN_DISENO_DIA.md
│   └── ESTADO_ACTUAL.md
├── specs/             # Nivel 2: Especificaciones técnicas
│   └── SPEC_FORK_MIN_DIA.md
├── modules/           # Nivel 2: Documentación de módulos
│   ├── cli/
│   │   ├── README.md
│   │   ├── git_ops.md
│   │   ├── sessions.md
│   │   ├── config.md
│   │   ├── templates.md
│   │   ├── ndjson.md
│   │   ├── utils.md
│   │   ├── rules.md
│   │   └── cursor_reminder.md
│   └── api/
│       └── endpoints.md
├── ui/                # Nivel 2: Documentación de UI
│   ├── App.md
│   ├── BoardView.md
│   ├── components/
│   │   ├── README.md
│   │   ├── BitacoraViewer.md
│   │   ├── BitacoraEditor.md
│   │   ├── SummariesViewer.md
│   │   ├── DocsViewer.md
│   │   ├── DocTreeNode.md
│   │   ├── MarkdownRenderer.md
│   │   ├── SessionObjectives.md
│   │   ├── ErrorFixCommitChain.md
│   │   ├── TemporalNotesViewer.md
│   │   └── BoardElement.md
│   └── design/
│       ├── ALTERNATIVAS_REFRESH.md
│       └── MEJORAS_VISUALIZACION_DOCS.md
├── guides/            # Nivel 3: Guías de herramientas
│   ├── dia-start.md
│   ├── dia-pre-feat.md
│   ├── dia-end.md
│   ├── dia-close-day.md
│   ├── dia-summarize.md
│   ├── dia-cap.md
│   ├── dia-fix.md
│   ├── workflow_error_fix_commit.md
│   ├── sesiones-multiples.md
│   ├── dia-desarrollo.md
│   ├── gestion-data.md
│   └── documentacion-scopes.md
└── manual/            # Nivel 1: Tutorial usuario
    ├── TUTORIAL_INTRO_V0_1.md
    └── CAPTURA_ERRORES.md
```

---

## Rutas de Aprendizaje

### Para Usuarios Nuevos

1. **[Resumen de diseño](overview/RESUMEN_DISENO_DIA.md)** — Entender qué es `/dia`
2. **[Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md)** — Aprender a usar
3. **[Guías de comandos](guides/)** — Referencia rápida por comando

### Para Desarrolladores

1. **[Resumen de diseño](overview/RESUMEN_DISENO_DIA.md)** — Entender arquitectura
2. **[Documentación de módulos CLI](modules/cli/README.md)** — Entender código
3. **[Documentación de componentes UI](ui/components/README.md)** — Entender componentes
4. **[Documentación de API](modules/api/endpoints.md)** — Entender endpoints
5. **[Estructura NDJSON](../dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))** — Entender formato de datos

### Para Contribuidores

1. **[Estado actual](overview/ESTADO_ACTUAL.md)** — Ver qué está implementado
2. **[Documentación de módulos](modules/)** — Entender estructura del código
3. **[Especificaciones](specs/)** — Ver qué falta implementar
4. **[Scopes de documentación](guides/documentacion-scopes.md)** — Cómo actualizar documentación

---

## Referencias Rápidas

- **Inicio rápido**: [README principal](../README.md)
- **Instalación**: [Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md#parte-1-instalación-y-verificación)
- **Comandos CLI**: [Guías de comandos](guides/)
- **API**: [Endpoints](modules/api/endpoints.md)
- **Formato de eventos**: [NDJSON](../dia%20—%20Estructura%20NDJSON%20de%20eventos%20(v0.1))
- **Gestión de datos**: [Guía de gestión de datos](guides/gestion-data.md)

---

## Mantenimiento

### Actualizar Documentación

Cuando cambies código, actualiza la documentación correspondiente siguiendo la estructura del proyecto:

- **Nuevo componente UI** (`ui/src/components/X.svelte`) → Crear `docs/ui/components/X.md`
- **Nuevo módulo CLI** (`cli/dia_cli/X.py`) → Crear `docs/modules/cli/X.md`
- **Nuevo endpoint API** → Actualizar `docs/modules/api/endpoints.md`
- **Nueva guía** → Agregar a `docs/guides/`

Ver [Scopes de documentación](guides/documentacion-scopes.md) para más detalles.

### Validar Links

Usa herramientas para verificar que todos los links funcionan después de reorganizaciones.

### Niveles Claros

Mantén la separación entre niveles de lectura:
- **Nivel 1**: Entendimiento general y tutoriales
- **Nivel 2**: Especificaciones y documentación técnica de módulos
- **Nivel 3**: Guías de herramientas y comandos

---

**Última actualización**: 2026-01-19
