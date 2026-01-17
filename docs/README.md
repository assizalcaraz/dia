# Documentación de /dia

**Versión**: v0.1  
**Última actualización**: 2026-01-18

Este directorio contiene toda la documentación del proyecto `/dia`, organizada en niveles de lectura claros.

---

## Niveles de Lectura

### Nivel 1: Entendimiento General

Documentación para entender qué es `/dia`, su filosofía y cómo empezar.

- **[Resumen de diseño](overview/RESUMEN_DISENO_DIA.md)** — Síntesis operativa del diseño y workflow
- **[Contexto inicial](overview/CONTEXTO_INICIAL.md)** — Diagnóstico, metodología y principios
- **[Estado actual](overview/ESTADO_ACTUAL.md)** — Estado técnico del proyecto

**Para empezar**: Lee el [Resumen de diseño](overview/RESUMEN_DISENO_DIA.md) y luego el [Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md).

---

### Nivel 2: Especificaciones Técnicas

Documentación técnica de formatos, estructuras y especificaciones.

- **[Estructura NDJSON de eventos](specs/NDJSON.md)** — Formato de eventos y catálogo completo
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

- **[Índice de componentes UI](modules/components/README.md)**
  - [`App.svelte`](modules/App.md) — Componente principal de la UI
  - [`BitacoraViewer`](modules/components/BitacoraViewer.md) — Visualizador de bitácoras
  - [`SummariesViewer`](modules/components/SummariesViewer.md) — Visualizador de resúmenes
  - [`DocsViewer`](modules/components/DocsViewer.md) — Visualizador de documentación
  - [`DocTreeNode`](modules/components/DocTreeNode.md) — Componente de árbol de documentación
  - [`MarkdownRenderer`](modules/components/MarkdownRenderer.md) — Renderizador de markdown

---

### Nivel 3: Guías de Herramientas

Guías específicas de cada comando y herramienta.

- **[`dia start`](guides/dia-start.md)** — Iniciar sesión
- **[`dia pre-feat`](guides/dia-pre-feat.md)** — Checkpoint pre-feat
- **[`dia end`](guides/dia-end.md)** — Cerrar sesión
- **[`dia close-day`](guides/dia-close-day.md)** — Cerrar jornada
- **[`dia cap`](guides/dia-cap.md)** — Capturar errores/logs
- **[`dia fix`](guides/dia-fix.md)** — Linkear fix a error

---

### Nivel 1: Tutorial de Usuario

Tutorial paso a paso para usuarios.

- **[Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md)** — Guía completa de uso

---

## Estructura del Directorio

```
docs/
├── README.md (este archivo)
├── overview/          # Nivel 1: Entendimiento general
│   ├── CONTEXTO_INICIAL.md
│   ├── RESUMEN_DISENO_DIA.md
│   └── ESTADO_ACTUAL.md
├── specs/             # Nivel 2: Especificaciones técnicas
│   ├── NDJSON.md
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
│   ├── api/
│   │   └── endpoints.md
│   ├── components/
│   │   ├── README.md
│   │   ├── BitacoraViewer.md
│   │   ├── SummariesViewer.md
│   │   ├── DocsViewer.md
│   │   ├── DocTreeNode.md
│   │   └── MarkdownRenderer.md
│   └── App.md
├── guides/            # Nivel 3: Guías de herramientas
│   ├── dia-start.md
│   ├── dia-pre-feat.md
│   ├── dia-end.md
│   ├── dia-close-day.md
│   ├── dia-cap.md
│   └── dia-fix.md
└── manual/            # Nivel 1: Tutorial usuario
    └── TUTORIAL_INTRO_V0_1.md
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
3. **[Documentación de componentes UI](modules/components/README.md)** — Entender componentes
4. **[Documentación de API](modules/api/endpoints.md)** — Entender endpoints
5. **[Estructura NDJSON](specs/NDJSON.md)** — Entender formato de datos

### Para Contribuidores

1. **[Estado actual](overview/ESTADO_ACTUAL.md)** — Ver qué está implementado
2. **[Documentación de módulos](modules/)** — Entender estructura del código
3. **[Especificaciones](specs/)** — Ver qué falta implementar

---

## Referencias Rápidas

- **Inicio rápido**: [README principal](../README.md)
- **Instalación**: [Tutorial completo](manual/TUTORIAL_INTRO_V0_1.md#parte-1-instalación-y-verificación)
- **Comandos CLI**: [Guías de comandos](guides/)
- **API**: [Endpoints](modules/api/endpoints.md)
- **Formato de eventos**: [NDJSON](specs/NDJSON.md)

---

## Mantenimiento

- **Actualizar documentación**: Cuando cambies código, actualiza la documentación correspondiente.
- **Validar links**: Usa herramientas para verificar que todos los links funcionan.
- **Niveles claros**: Mantén la separación entre niveles de lectura.

---

**Última actualización**: 2026-01-18
