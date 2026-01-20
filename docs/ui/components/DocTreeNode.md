# DocTreeNode

**Ubicación**: `ui/src/components/DocTreeNode.svelte`  
**Versión**: v0.1

Componente Svelte recursivo para renderizar nodos del árbol de documentación.

---

## Props

- `node` (object, requerido): Nodo del árbol (tipo `directory` o `file`)
  - `name`: Nombre del nodo
  - `type`: Tipo (`"directory"` o `"file"`)
  - `path`: Ruta del nodo
  - `children`: Array de nodos hijos (solo para directorios)
- `path` (string, default: `""`): Ruta del nodo
- `level` (number, default: `0`): Nivel de anidación (para indentación)
- `selectedPath` (string | null, default: `null`): Ruta del documento seleccionado
- `expandedNodes` (object, default: `{}`): Objeto que rastrea nodos expandidos
- `isExpanded` (function, default: `() => false`): Función para verificar si un nodo está expandido
- `toggleNode` (function, default: `() => {}`): Función para alternar expansión de un nodo

---

## Funcionalidad

1. **Renderizado recursivo**: Usa `<svelte:self>` para renderizar nodos hijos
2. **Iconos visuales**: Muestra 📁 para directorios colapsados, 📂 para expandidos, 📄 para archivos
3. **Interacción**: Al hacer clic en un archivo, dispara evento `select`. Al hacer clic en un directorio, alterna su expansión
4. **Indentación**: Aplica padding según nivel de anidación
5. **Estado seleccionado**: Resalta el archivo actualmente seleccionado

---

## Eventos

- `select` (detail: `string`): Disparado cuando se selecciona un archivo. El detail contiene la ruta del archivo.

---

## Comportamiento

- Los directorios se pueden expandir/colapsar haciendo clic
- Los archivos se pueden seleccionar haciendo clic
- El componente se renderiza recursivamente para nodos hijos
- La indentación aumenta con cada nivel de anidación

---

## Ejemplo de uso

```svelte
<DocTreeNode
  node={node}
  path={node.path}
  level={0}
  selectedPath={selectedDoc}
  expandedNodes={expandedNodes}
  isExpanded={isExpanded}
  toggleNode={toggleNode}
  on:select={(e) => loadDocContent(e.detail)}
/>
```

---

## Referencias

- [DocsViewer](./DocsViewer.md) — Componente que usa DocTreeNode
- [Documentación de API](../api/endpoints.md) — Endpoints de la API
