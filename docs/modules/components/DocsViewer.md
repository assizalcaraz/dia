# DocsViewer

**Ubicación**: `ui/src/components/DocsViewer.svelte`  
**Versión**: v0.1

Componente Svelte para visualizar la documentación del proyecto en formato de árbol navegable.

---

## Props

- `apiBase` (string, default: `"/api"`): Base URL de la API

---

## Funcionalidad

1. **Carga de árbol de documentación**: Obtiene estructura de directorios y archivos desde `/api/docs/list/`
2. **Navegación en árbol**: Permite expandir/colapsar directorios y seleccionar archivos
3. **Búsqueda**: Permite filtrar documentos por nombre
4. **Vista de contenido**: Muestra contenido markdown del documento seleccionado
5. **Breadcrumbs**: Muestra ruta del documento actual
6. **Layout dividido**: Muestra árbol a la izquierda y contenido a la derecha

---

## Dependencias

- `DocTreeNode`: Componente recursivo para renderizar nodos del árbol
- `MarkdownRenderer`: Componente para renderizar contenido markdown

---

## Integración con API

### Endpoints utilizados

- `GET /api/docs/list/` — Obtiene estructura de árbol de documentación
- `GET /api/docs/{path}/` — Obtiene contenido markdown del documento especificado

---

## Estados

- `docsTree`: Estructura de árbol de documentación
- `selectedDoc`: Ruta del documento actualmente seleccionado
- `content`: Contenido markdown del documento seleccionado
- `loading`: Estado de carga del árbol
- `loadingContent`: Estado de carga de contenido
- `error`: Mensaje de error (si existe)
- `expandedNodes`: Objeto que rastrea qué nodos están expandidos
- `searchQuery`: Texto de búsqueda para filtrar documentos
- `filteredTree`: Árbol filtrado según búsqueda

---

## Comportamiento

- Al montar el componente, carga automáticamente el árbol de documentación
- El nodo raíz se expande automáticamente
- Al buscar, expande automáticamente todos los directorios con resultados
- Al seleccionar un documento, expande automáticamente su ruta en el árbol
- Layout responsive: en móviles se apila verticalmente

---

## Funciones auxiliares

- `filterTree(tree, query)`: Filtra el árbol de documentación según query de búsqueda
- `expandAll(tree)`: Expande todos los nodos del árbol
- `toggleNode(path)`: Alterna estado de expansión de un nodo
- `isExpanded(path)`: Verifica si un nodo está expandido

---

## Ejemplo de uso

```svelte
<DocsViewer apiBase="/api" />
```

---

## Referencias

- [DocTreeNode](./DocTreeNode.md) — Componente de nodo de árbol
- [MarkdownRenderer](./MarkdownRenderer.md) — Componente de renderizado markdown
- [Documentación de API](../api/endpoints.md) — Endpoints de la API
