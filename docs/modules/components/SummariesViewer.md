# SummariesViewer

**Ubicación**: `ui/src/components/SummariesViewer.svelte`  
**Versión**: v0.1

Componente Svelte para visualizar resúmenes regenerables (rolling/nightly) del sistema `/dia`.

---

## Props

- `apiBase` (string, default: `"/api"`): Base URL de la API
- `initialDayId` (string | null, default: `null`): ID del día inicial a mostrar (formato `YYYY-MM-DD`)

---

## Funcionalidad

1. **Carga de días disponibles**: Obtiene lista de días con resúmenes desde `/api/summaries/`
2. **Selector de día**: Permite seleccionar un día específico para ver sus resúmenes
3. **Lista de resúmenes**: Muestra lista de resúmenes disponibles (rolling/nightly) con su assessment
4. **Vista de contenido**: Permite seleccionar un resumen y ver su contenido markdown renderizado
5. **Layout dividido**: Muestra lista de resúmenes a la izquierda y contenido a la derecha

---

## Dependencias

- `MarkdownRenderer`: Componente para renderizar contenido markdown

---

## Integración con API

### Endpoints utilizados

- `GET /api/summaries/` — Obtiene lista de resúmenes para extraer días disponibles
- `GET /api/summaries/{day_id}/list/` — Obtiene lista de resúmenes del día especificado
- `GET /api/summaries/{day_id}/{summary_id}/content/` — Obtiene contenido markdown del resumen

---

## Estados

- `availableDays`: Array de días disponibles (formato `YYYY-MM-DD`)
- `selectedDayId`: Día actualmente seleccionado
- `summaries`: Array de resúmenes del día seleccionado
- `selectedSummary`: Resumen actualmente seleccionado
- `content`: Contenido markdown del resumen seleccionado
- `loading`: Estado de carga de resúmenes
- `loadingContent`: Estado de carga de contenido
- `error`: Mensaje de error (si existe)

---

## Comportamiento

- Al montar el componente, carga automáticamente los días disponibles
- Al cambiar `selectedDayId`, carga automáticamente los resúmenes del día
- Al seleccionar un resumen, carga automáticamente su contenido
- Muestra emoji de assessment (✅ ON_TRACK, ⚠️ OFF_TRACK, 🚫 BLOCKED)
- Layout responsive: en móviles se apila verticalmente

---

## Ejemplo de uso

```svelte
<SummariesViewer apiBase="/api" initialDayId="2026-01-17" />
```

---

## Referencias

- [MarkdownRenderer](./MarkdownRenderer.md) — Componente de renderizado markdown
- [Documentación de API](../api/endpoints.md) — Endpoints de la API
