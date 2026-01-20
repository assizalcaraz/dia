# BitacoraViewer

**Ubicación**: `ui/src/components/BitacoraViewer.svelte`  
**Versión**: v0.1

Componente Svelte para visualizar bitácoras de jornada del sistema `/dia`.

---

## Props

- `apiBase` (string, default: `"/api"`): Base URL de la API
- `initialDayId` (string | null, default: `null`): ID del día inicial a mostrar (formato `YYYY-MM-DD`)

---

## Funcionalidad

1. **Carga de días disponibles**: Obtiene lista de días con sesiones desde `/api/sessions/`
2. **Selector de día**: Permite seleccionar un día específico para ver su bitácora
3. **Carga de bitácora**: Obtiene contenido de la bitácora desde `/api/jornada/{day_id}/`
4. **Renderizado**: Usa `MarkdownRenderer` para mostrar el contenido markdown de la bitácora

---

## Dependencias

- `MarkdownRenderer`: Componente para renderizar contenido markdown

---

## Integración con API

### Endpoints utilizados

- `GET /api/sessions/` — Obtiene lista de sesiones para extraer días disponibles
- `GET /api/jornada/{day_id}/` — Obtiene contenido de la bitácora del día especificado

---

## Estados

- `availableDays`: Array de días disponibles (formato `YYYY-MM-DD`)
- `selectedDayId`: Día actualmente seleccionado
- `content`: Contenido markdown de la bitácora
- `loading`: Estado de carga
- `error`: Mensaje de error (si existe)

---

## Comportamiento

- Al montar el componente, carga automáticamente los días disponibles
- Al cambiar `selectedDayId`, carga automáticamente la bitácora correspondiente
- Si el día seleccionado no está en la lista de disponibles, se agrega al selector
- Muestra estados de carga, error y vacío según corresponda

---

## Ejemplo de uso

```svelte
<BitacoraViewer apiBase="/api" initialDayId="2026-01-17" />
```

---

## Referencias

- [MarkdownRenderer](./MarkdownRenderer.md) — Componente de renderizado markdown
- [Documentación de API](../api/endpoints.md) — Endpoints de la API
