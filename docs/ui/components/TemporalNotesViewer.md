# TemporalNotesViewer

**Ubicación**: `ui/src/components/TemporalNotesViewer.svelte`  
**Versión**: v0.1

Componente para visualizar notas temporales del día. Permite navegar entre archivos de notas y ver su contenido renderizado en markdown.

---

## Propósito

Visualiza notas temporales almacenadas en `docs_temp/`:
- Lista de archivos de notas del día
- Navegación entre notas
- Visualización de contenido en markdown
- Soporte para múltiples archivos

---

## Props

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `apiBase` | `string` | `"/api"` | Base URL de la API |
| `dayId` | `string \| null` | `null` | ID del día (formato `YYYY-MM-DD`) |

---

## Funcionalidad

### Carga de Notas

- **Lista de archivos**: Carga lista de archivos de notas del día desde la API
- **Carga bajo demanda**: Carga contenido de un archivo solo cuando se selecciona
- **Manejo de errores**: Maneja graciosamente cuando no hay notas (404)

### Navegación

- **Lista lateral**: Muestra lista de archivos disponibles
- **Selección**: Permite seleccionar un archivo para ver su contenido
- **Indicador visual**: Muestra qué archivo está seleccionado

### Visualización

- **Renderizado markdown**: Usa `MarkdownRenderer` para mostrar contenido formateado
- **Contenido vacío**: Muestra mensaje cuando no hay contenido

---

## Integración con API

### Endpoints utilizados

- `GET /api/notes/tmp/{day_id}/` — Obtiene lista de archivos de notas del día
- `GET /api/notes/tmp/{day_id}/{filename}` — Obtiene contenido de un archivo de nota

---

## Estados

- `files`: Array de nombres de archivos de notas
- `selectedFile`: Nombre del archivo actualmente seleccionado
- `selectedContent`: Contenido del archivo seleccionado
- `loading`: Indica si se está cargando
- `error`: Mensaje de error si ocurre algún problema

---

## Comportamiento

- **Al montar**: Carga lista de archivos del día especificado
- **Al cambiar `dayId`**: Recarga lista de archivos del nuevo día
- **Al seleccionar archivo**: Carga contenido del archivo seleccionado
- **Sin notas**: Muestra mensaje informativo cuando no hay notas disponibles

---

## Dependencias

- `MarkdownRenderer`: Para renderizar contenido markdown de las notas

---

## Ejemplo de uso

```svelte
<TemporalNotesViewer apiBase="/api" dayId="2026-01-19" />
```

---

## Referencias

- [MarkdownRenderer](./MarkdownRenderer.md) — Componente de renderizado de markdown
- [App](../App.md) — Componente principal que usa este componente
- [Documentación de API](../../modules/api/endpoints.md#notes) — Endpoints de notas temporales
