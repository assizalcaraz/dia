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
- **Errores abiertos**: Lista de errores sin fix

---

## Funcionalidad

1. **Auto-refresh**: Recarga datos cada 5 segundos
2. **Carga inicial**: Carga todos los datos al montar el componente
3. **Navegación por tabs**: Permite cambiar entre vistas en la zona indeleble
4. **Visualización de métricas**: Muestra contadores de sesiones, resúmenes y errores
5. **Timeline de veredictos**: Muestra evolución de assessments rolling con indicadores de cambio

---

## Dependencias

- `BitacoraViewer`: Componente para visualizar bitácoras
- `SummariesViewer`: Componente para visualizar resúmenes
- `DocsViewer`: Componente para visualizar documentación

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
- `loading`: Estado de carga
- `today`: ID del día actual (formato `YYYY-MM-DD`)
- `activeTab`: Tab activo en zona indeleble (`"overview"`, `"bitacora"`, `"summaries"`, `"docs"`)

---

## Funciones auxiliares

- `fetchJson(path)`: Función helper para hacer requests a la API
- `getAssessmentEmoji(assessment)`: Retorna emoji según assessment (✅ ON_TRACK, ⚠️ OFF_TRACK, 🚫 BLOCKED)
- `load()`: Carga todos los datos de la API
- `formatElapsed(minutes)`: Formatea duración en minutos a formato legible

---

## Comportamiento

- Al montar, carga todos los datos y establece intervalo de refresh cada 5 segundos
- Al desmontar, limpia el intervalo
- Muestra estados de carga mientras se obtienen datos
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
- [Documentación de API](./api/endpoints.md) — Endpoints de la API
