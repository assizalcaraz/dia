# App

**Ubicación**: `ui/src/App.svelte`  
**Versión**: v0.1

Componente principal de la UI del sistema `/dia`. Implementa la interfaz de "Zona indeleble" y "Zona viva".

---

## Estructura

El componente se divide en dos secciones principales:

### Zona indeleble

Panel izquierdo que muestra:
- **Resumen**: Métricas del día, timeline de veredictos rolling
- **Bitácora**: Visualizador de bitácoras de jornada (usando `BitacoraViewer`)
- **Resúmenes**: Visualizador de resúmenes regenerables (usando `SummariesViewer`)
- **Documentación**: Visualizador de documentación del proyecto (usando `DocsViewer`)

### Zona viva

Panel derecho que muestra:
- **Sesión activa**: Información de la sesión actual
- **Sesiones de hoy**: Lista de sesiones del día con duración
- **Checklist diario**: Lista de verificación
- **Último resumen rolling**: Estado actual y próximo paso
- **Errores abiertos**: Lista de errores sin fix con tooltips interactivos
  - Tooltips con información detallada del error
  - Botón de copiar (📋) para copiar información del error al portapapeles
  - Tooltip permanece visible con delay y fade out suave

---

## Funcionalidad

1. **Auto-refresh incremental**: Actualiza datos cada 5 segundos sin causar parpadeo
   - Usa actualización silenciosa que preserva estado de UI (tooltips, scroll)
   - Pausa automáticamente cuando la ventana no está visible (Page Visibility API)
   - Solo muestra indicador de carga en la carga inicial
2. **Carga inicial**: Carga todos los datos al montar el componente
3. **Navegación por tabs**: Permite cambiar entre vistas en la zona indeleble
4. **Visualización de métricas**: Muestra contadores de sesiones, resúmenes y errores
5. **Timeline de veredictos**: Muestra evolución de assessments rolling con indicadores de cambio
6. **Preservación de estado**: Mantiene posición de scroll y tooltips abiertos durante actualizaciones
7. **Tooltips de errores interactivos**: 
   - Muestra información detallada al hacer hover sobre errores
   - Botón de copiar para copiar información al portapapeles
   - Delay de 500ms antes de cerrar con fade out suave de 200ms
   - Permite interacción completa (hover y click) sin que se cierre prematuramente

---

## Dependencias

- `BitacoraViewer`: Componente para visualizar bitácoras
- `SummariesViewer`: Componente para visualizar resúmenes
- `DocsViewer`: Componente para visualizar documentación
- `BoardView`: Componente para Feature Board fullscreen (condicional, se muestra cuando `boardOpen` es `true`)

---

## Integración con API

### Endpoints utilizados

- `GET /api/sessions/` — Lista de sesiones
- `GET /api/sessions/current/` — Sesión activa
- `GET /api/summaries/` — Lista de resúmenes
- `GET /api/summaries/latest/?day_id={today}&mode=rolling` — Último resumen rolling
- `GET /api/summaries/?day_id={today}&mode=rolling&limit=20` — Timeline de veredictos
- `GET /api/metrics/` — Métricas generales
- `GET /api/captures/errors/open/` — Errores abiertos
- `GET /api/day/today/` — Información del día actual

---

## Estados

- `sessions`: Array de sesiones
- `currentSession`: Sesión activa actual
- `summaries`: Array de resúmenes
- `latestRollingSummary`: Último resumen rolling del día
- `rollingTimeline`: Timeline de veredictos rolling
- `metrics`: Métricas generales
- `openErrors`: Array de errores abiertos
- `dayToday`: Información del día actual
- `loading`: Estado de carga (solo usado en carga inicial)
- `today`: ID del día actual (formato `YYYY-MM-DD`)
- `activeTab`: Tab activo en zona indeleble (`"overview"`, `"bitacora"`, `"summaries"`, `"docs"`)
- `zonaVivaElement`: Referencia al contenedor de zona viva (para preservar scroll)
- `boardOpen`: Control de visibilidad del Feature Board

---

## Funciones auxiliares

- `fetchJson(path)`: Función helper para hacer requests a la API
- `getAssessmentEmoji(assessment)`: Retorna emoji según assessment (✅ ON_TRACK, ⚠️ OFF_TRACK, 🚫 BLOCKED)
- `load()`: Carga inicial completa de todos los datos (con indicador de carga)
- `loadIncremental()`: Actualización silenciosa que preserva estado de UI (sin parpadeo)
- `formatElapsed(minutes)`: Formatea duración en minutos a formato legible
- `copyErrorContent(error)`: Copia información del error al portapapeles (título, sesión, fecha, artifact, hash)
- `handleErrorTooltipPosition(event, tooltipElement)`: Calcula y posiciona tooltip de error de forma inteligente

---

## Comportamiento

- **Al montar**: 
  - Carga inicial completa con indicador de carga
  - Establece intervalo de actualización incremental cada 5 segundos
  - Escucha cambios de visibilidad de la página (Page Visibility API)
- **Durante actualizaciones incrementales**:
  - Actualiza datos sin mostrar indicador de carga (sin parpadeo)
  - Preserva posición de scroll de la zona viva
  - No cierra tooltips abiertos
- **Cuando la ventana no está visible**: Pausa el polling automáticamente
- **Al volver a la ventana**: Carga datos frescos y reanuda polling
- **Al desmontar**: Limpia intervalos y event listeners
- Muestra estados de carga solo en la carga inicial
- Muestra mensajes informativos cuando no hay datos disponibles
- El botón "Regenerar ahora" muestra un alert con el comando sugerido (no ejecuta comandos)

---

## Ejemplo de uso

```svelte
<!-- App.svelte es el componente raíz, se usa directamente -->
```

---

## Referencias

- [BitacoraViewer](./components/BitacoraViewer.md) — Componente de bitácoras
- [SummariesViewer](./components/SummariesViewer.md) — Componente de resúmenes
- [DocsViewer](./components/DocsViewer.md) — Componente de documentación
- [BoardView](./ui/BoardView.md) — Componente de Feature Board
- [ALTERNATIVAS_REFRESH.md](./ui/ALTERNATIVAS_REFRESH.md) — Documentación sobre el sistema de actualización incremental
- [Documentación de API](./api/endpoints.md) — Endpoints de la API
