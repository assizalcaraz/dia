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

### Componente Principal

- **[`App`](../App.md)** — Componente principal de la UI (ubicado en `ui/src/App.svelte`)

---

## Estructura de Componentes

```
ui/src/
├── App.svelte              # Componente principal
└── components/
    ├── BitacoraViewer.svelte
    ├── SummariesViewer.svelte
    ├── DocsViewer.svelte
    ├── DocTreeNode.svelte
    └── MarkdownRenderer.svelte
```

---

## Dependencias entre Componentes

```
App.svelte
├── BitacoraViewer
│   └── MarkdownRenderer
├── SummariesViewer
│   └── MarkdownRenderer
└── DocsViewer
    ├── DocTreeNode (recursivo)
    └── MarkdownRenderer
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

## Referencias

- [Documentación de módulos CLI](../cli/README.md)
- [Documentación de API](../api/endpoints.md)
- [Guías de comandos](../../guides/)
