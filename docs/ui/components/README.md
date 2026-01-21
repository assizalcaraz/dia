# Documentación de Componentes UI

**Versión**: v0.1  
**Ubicación**: `ui/src/components/`

Este directorio contiene la documentación técnica de los componentes Svelte de la UI de `/dia`.

---

## Componentes

### Componentes de Visualización

- **[`BitacoraViewer`](./BitacoraViewer.md)** — Visualizador de bitácoras de jornada
- **[`SummariesViewer`](./SummariesViewer.md)** — Visualizador de resúmenes regenerables (rolling/nightly)
- **[`DocsViewer`](./DocsViewer.md)** — Visualizador de documentación del proyecto

### Componentes de UI

- **[`DocTreeNode`](./DocTreeNode.md)** — Componente recursivo para árbol de documentación
- **[`MarkdownRenderer`](./MarkdownRenderer.md)** — Renderizador de contenido markdown

### Componentes de Edición

- **[`BitacoraEditor`](./BitacoraEditor.md)** — Editor de bitácoras diarias (secciones editables)

### Componentes de Sesión

- **[`SessionObjectives`](./SessionObjectives.md)** — Visualizador de objetivos de sesión (Intent y DoD)
- **[`ErrorFixCommitChain`](./ErrorFixCommitChain.md)** — Visualizador de cadena Error→Fix→Commit
- **[`TemporalNotesViewer`](./TemporalNotesViewer.md)** — Visualizador de notas temporales

### Feature Board

- **[`BoardView`](../BoardView.md)** — Feature Board fullscreen con canvas interactivo
- **[`BoardElement`](./BoardElement.md)** — Componente para renderizar elementos del board

### Componente Principal

- **[`App`](../App.md)** — Componente principal de la UI (ubicado en `ui/src/App.svelte`)

---

## Estructura de Componentes

```
ui/src/
├── App.svelte              # Componente principal
└── components/
    ├── BitacoraViewer.svelte
    ├── BitacoraEditor.svelte
    ├── SummariesViewer.svelte
    ├── DocsViewer.svelte
    ├── DocTreeNode.svelte
    ├── MarkdownRenderer.svelte
    ├── SessionObjectives.svelte
    ├── ErrorFixCommitChain.svelte
    ├── TemporalNotesViewer.svelte
    ├── BoardView.svelte    # Feature Board (v0.2)
    └── BoardElement.svelte # Elementos del board (v0.2)
```

---

## Dependencias entre Componentes

```
App.svelte
├── BitacoraViewer
│   └── MarkdownRenderer
├── BitacoraEditor
│   └── MarkdownRenderer
├── SummariesViewer
│   └── MarkdownRenderer
├── DocsViewer
│   ├── DocTreeNode (recursivo)
│   └── MarkdownRenderer
├── SessionObjectives
├── ErrorFixCommitChain
├── TemporalNotesViewer
└── BoardView (condicional)
    └── BoardElement
```

**Nota**: `MarkdownRenderer` es usado por múltiples componentes para renderizar contenido markdown.

---

## Integración con API

Todos los componentes que requieren datos se comunican con la API Django a través de endpoints REST:

- **BitacoraViewer**: `/api/sessions/`, `/api/jornada/{day_id}/`
- **SummariesViewer**: `/api/summaries/`, `/api/summaries/{day_id}/list/`, `/api/summaries/{day_id}/{summary_id}/content/`
- **DocsViewer**: `/api/docs/list/`, `/api/docs/{path}/`

Ver [Documentación de API](../api/endpoints.md) para detalles completos.

---

## Sistema de Actualización

El componente principal `App.svelte` implementa un sistema de actualización incremental que:

- Actualiza datos cada 5 segundos sin causar parpadeo
- Preserva estado de UI (tooltips, scroll, selecciones)
- Pausa automáticamente cuando la ventana no está visible
- Solo muestra indicador de carga en la carga inicial

Ver [ALTERNATIVAS_REFRESH.md](../design/ALTERNATIVAS_REFRESH.md) para documentación completa del sistema.

---

## Referencias

- [Documentación de módulos CLI](../../modules/cli/README.md)
- [Documentación de API](../../modules/api/endpoints.md)
- [Guías de comandos](../../guides/)
- [Sistema de actualización incremental](../design/ALTERNATIVAS_REFRESH.md)
