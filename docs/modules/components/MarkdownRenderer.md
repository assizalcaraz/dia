# MarkdownRenderer

**Ubicación**: `ui/src/components/MarkdownRenderer.svelte`  
**Versión**: v0.1

Componente Svelte para renderizar contenido markdown con estilos personalizados.

---

## Props

- `content` (string, default: `""`): Contenido markdown a renderizar

---

## Funcionalidad

1. **Parsing de markdown**: Usa la librería `marked` para convertir markdown a HTML
2. **Renderizado seguro**: Usa `{@html}` de Svelte para renderizar HTML generado
3. **Estilos personalizados**: Aplica estilos CSS personalizados para todos los elementos markdown
4. **Manejo de errores**: Muestra mensaje de error si falla el parsing

---

## Dependencias

- `marked`: Librería para parsing de markdown

---

## Configuración de marked

- `breaks: true`: Convierte saltos de línea simples en `<br>`
- `gfm: true`: Habilita GitHub Flavored Markdown

---

## Elementos estilizados

- **Encabezados** (h1-h6): Tamaños y márgenes personalizados
- **Párrafos**: Espaciado y color
- **Listas** (ul, ol): Padding y márgenes
- **Código inline**: Fondo, padding y borde
- **Bloques de código**: Fondo, borde y scroll horizontal
- **Citas** (blockquote): Borde izquierdo y estilo itálico
- **Enlaces**: Color y subrayado
- **Tablas**: Bordes y espaciado
- **Separadores** (hr): Borde superior

---

## Estados

- `htmlContent`: HTML generado a partir del markdown

---

## Comportamiento

- Re-renderiza automáticamente cuando cambia `content`
- Muestra mensaje de error si falla el parsing
- Aplica estilos CSS usando variables CSS del tema

---

## Ejemplo de uso

```svelte
<MarkdownRenderer content="# Título\n\nContenido markdown aquí." />
```

---

## Referencias

- [BitacoraViewer](./BitacoraViewer.md) — Usa MarkdownRenderer
- [SummariesViewer](./SummariesViewer.md) — Usa MarkdownRenderer
- [DocsViewer](./DocsViewer.md) — Usa MarkdownRenderer
