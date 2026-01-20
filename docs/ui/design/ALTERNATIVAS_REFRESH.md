# Alternativas al Refresh Programado

**Fecha**: 2026-01-17  
**Problema**: El refresh programado cada 5 segundos causa parpadeo y cierra tooltips de errores

---

## Problema Actual

El sistema actual usa `setInterval(load, 5000)` que:
- ❌ Establece `loading = true` en cada refresh, causando parpadeo
- ❌ Resetea el estado de la UI, cerrando tooltips abiertos
- ❌ Puede afectar el scroll de la zona viva
- ❌ Recarga todos los datos aunque no hayan cambiado

---

## Alternativas Evaluadas

### 1. Actualización Incremental (✅ RECOMENDADA)

**Ventajas**:
- ✅ No causa parpadeo (no usa `loading = true` global)
- ✅ Solo actualiza datos que cambiaron
- ✅ Preserva estado de UI (tooltips, scroll)
- ✅ Más eficiente (menos requests innecesarios)
- ✅ Fácil de implementar

**Implementación**:
- Separar `loading` por sección (sessions, summaries, errors, etc.)
- Comparar timestamps o checksums antes de actualizar
- Usar actualización silenciosa (sin indicador de carga)
- Preservar estado de scroll y tooltips

**Complejidad**: Baja  
**Impacto**: Alto

---

### 2. Server-Sent Events (SSE)

**Ventajas**:
- ✅ Actualización en tiempo real
- ✅ No requiere polling constante
- ✅ Eficiente en recursos

**Desventajas**:
- ⚠️ Requiere cambios en el backend (Django)
- ⚠️ Más complejo de implementar
- ⚠️ Requiere manejo de reconexión

**Complejidad**: Media-Alta  
**Impacto**: Alto (pero requiere backend)

---

### 3. WebSockets

**Ventajas**:
- ✅ Actualización bidireccional en tiempo real
- ✅ Muy eficiente

**Desventajas**:
- ⚠️ Requiere infraestructura adicional (Django Channels)
- ⚠️ Más complejo de mantener
- ⚠️ Overkill para este caso de uso

**Complejidad**: Alta  
**Impacto**: Alto (pero excesivo para este caso)

---

### 4. Polling Inteligente

**Ventajas**:
- ✅ Solo actualiza cuando la ventana está activa (Page Visibility API)
- ✅ Ajusta frecuencia según actividad
- ✅ Mantiene simplicidad del polling

**Implementación**:
- Pausar cuando `document.hidden === true`
- Aumentar intervalo si no hay cambios
- Reducir intervalo si hay actividad reciente

**Complejidad**: Baja  
**Impacto**: Medio

---

### 5. Actualización por Eventos del Usuario

**Ventajas**:
- ✅ Solo actualiza cuando el usuario interactúa
- ✅ No consume recursos en background

**Desventajas**:
- ⚠️ Puede mostrar datos desactualizados
- ⚠️ No es "tiempo real"

**Complejidad**: Baja  
**Impacto**: Bajo (no cumple requisito de tiempo real)

---

## Solución Recomendada: Híbrida

Combinar **Actualización Incremental** + **Polling Inteligente**:

1. **Actualización incremental**: No usar `loading = true` global, actualizar solo datos que cambiaron
2. **Page Visibility API**: Pausar cuando la ventana no está activa
3. **Preservar estado**: Mantener scroll, tooltips y selecciones
4. **Actualización silenciosa**: Sin indicadores de carga visibles

---

## Implementación

### Cambios en `App.svelte`

1. **Separar estados de carga**:
```javascript
let loadingSessions = false;
let loadingSummaries = false;
let loadingErrors = false;
// ... en lugar de un solo `loading`
```

2. **Actualización incremental**:
```javascript
const loadIncremental = async () => {
  // Solo actualizar si hay cambios detectados
  // No poner loading = true
  // Preservar estado de UI
};
```

3. **Page Visibility API**:
```javascript
onMount(() => {
  load();
  let intervalId;
  
  const startPolling = () => {
    intervalId = setInterval(loadIncremental, 5000);
  };
  
  const stopPolling = () => {
    if (intervalId) clearInterval(intervalId);
  };
  
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      stopPolling();
    } else {
      load(); // Cargar datos frescos al volver
      startPolling();
    }
  });
  
  startPolling();
  return () => {
    stopPolling();
    document.removeEventListener('visibilitychange', ...);
  };
});
```

4. **Preservar scroll**:
```javascript
// Guardar posición de scroll antes de actualizar
const scrollTop = zonaVivaElement?.scrollTop || 0;
// ... actualizar datos ...
// Restaurar posición después
requestAnimationFrame(() => {
  if (zonaVivaElement) {
    zonaVivaElement.scrollTop = scrollTop;
  }
});
```

---

## Comparación de Soluciones

| Solución | Complejidad | Eficiencia | Tiempo Real | Parpadeo | Preserva UI |
|----------|-------------|------------|-------------|----------|-------------|
| **Actual (setInterval)** | Baja | Media | ✅ | ❌ | ❌ |
| **Incremental** | Baja | Alta | ✅ | ✅ | ✅ |
| **SSE** | Media | Alta | ✅ | ✅ | ✅ |
| **WebSockets** | Alta | Alta | ✅ | ✅ | ✅ |
| **Polling Inteligente** | Baja | Media-Alta | ✅ | ⚠️ | ⚠️ |
| **Híbrida (Recomendada)** | Baja-Media | Alta | ✅ | ✅ | ✅ |

---

## Próximos Pasos

1. ✅ Implementar actualización incremental
2. ✅ Agregar Page Visibility API
3. ✅ Preservar estado de scroll y tooltips
4. ⏳ Evaluar SSE si se necesita más tiempo real
5. ⏳ Considerar WebSockets solo si hay necesidad bidireccional

---

**Última actualización**: 2026-01-17
