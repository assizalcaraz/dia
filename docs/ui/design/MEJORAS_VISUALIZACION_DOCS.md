# Mejoras de Visualización de Documentación

**Fecha**: 2026-01-18  
**Problema**: La zona indeleble es muy angosta para visualizar la documentación correctamente.

---

## Problema Identificado

La estructura actual del layout tiene las siguientes limitaciones:

1. **Layout de 2 columnas**: `.page` usa `grid-template-columns: 1fr 1fr` (50% cada columna)
2. **Zona indeleble limitada**: Ocupa solo la mitad del ancho disponible
3. **Layout interno de DocsViewer**: Tiene sidebar de 300px + contenido, reduciendo aún más el espacio
4. **Resultado**: El contenido de documentación queda muy angosto, dificultando la lectura

---

## Solución Implementada: Layout 70/30

### Descripción

Cuando se selecciona el tab "Documentación", el layout cambia a una distribución 70/30: la zona indeleble (documentación) ocupa el 70% del ancho y la zona viva el 30% restante.

### Cambios Realizados

1. **CSS (`app.css`)**:
   - Agregada clase `.docs-fullscreen` que cambia el layout a `grid-template-columns: 7fr 3fr`
   - La zona indeleble ocupa 70% del ancho cuando está activa
   - La zona viva se mantiene visible ocupando 30% del ancho

2. **App.svelte**:
   - Agregada clase condicional `docs-fullscreen` al contenedor `.page` cuando `activeTab === "docs"`
   - La zona viva siempre se muestra (no se oculta)

3. **DocsViewer.svelte**:
   - Aumentado el ancho del sidebar a 350px en pantallas grandes (≥1200px)
   - Aumentada la altura máxima del contenido a 85vh en modo fullscreen

### Ventajas

- ✅ **Más espacio para documentación**: 70% del ancho disponible (vs 50% anterior)
- ✅ **Zona viva siempre visible**: Se mantiene visible para consultar sesión activa, errores, etc.
- ✅ **Implementación simple**: Cambios mínimos en el código existente
- ✅ **Transición suave**: El cambio de layout es automático y fluido
- ✅ **No rompe funcionalidad**: Los otros tabs funcionan normalmente

### Desventajas

- ⚠️ La zona viva queda más estrecha (30% vs 50% anterior), pero sigue siendo funcional

---

## Alternativas Consideradas

### Alternativa 2: Layout Dinámico de 3 Columnas

**Descripción**: Cambiar a 3 columnas cuando se muestra documentación (sidebar docs | contenido docs | zona viva).

**Ventajas**:
- Mantiene la zona viva visible
- Mejor uso del espacio horizontal

**Desventajas**:
- Más complejo de implementar
- Puede ser confuso el cambio de layout
- En pantallas pequeñas requiere más ajustes responsive

**Código propuesto**:
```css
.page.docs-mode {
  grid-template-columns: 300px 1fr 400px;
}
```

---

### Alternativa 3: Modal/Overlay Fullscreen

**Descripción**: Abrir la documentación en un modal que ocupa toda la pantalla con botón de cerrar.

**Ventajas**:
- Experiencia inmersiva
- No afecta el layout principal
- Puede incluir controles adicionales (zoom, tema, etc.)

**Desventajas**:
- Requiere más código (gestión de estado del modal)
- Puede ser menos intuitivo para algunos usuarios
- Necesita manejo de teclas (ESC para cerrar)

**Código propuesto**:
```svelte
{#if showDocsModal}
  <div class="docs-modal">
    <button on:click={() => showDocsModal = false}>Cerrar</button>
    <DocsViewer />
  </div>
{/if}
```

---

### Alternativa 4: Botón "Expandir" en DocsViewer

**Descripción**: Agregar un botón dentro de DocsViewer para alternar entre modo normal y fullscreen.

**Ventajas**:
- Control explícito del usuario
- No cambia automáticamente el layout
- Puede aplicarse a otros viewers también

**Desventajas**:
- Requiere acción del usuario
- Puede no ser descubierto fácilmente

**Código propuesto**:
```svelte
<button on:click={() => isFullscreen = !isFullscreen}>
  {isFullscreen ? 'Contraer' : 'Expandir'}
</button>
```

---

## Recomendaciones Futuras

1. **Botón de toggle**: Agregar un botón para alternar entre modo normal y fullscreen manualmente
2. **Persistencia**: Guardar preferencia del usuario en localStorage
3. **Atajos de teclado**: Agregar `F` para fullscreen, `ESC` para salir
4. **Aplicar a otros viewers**: Considerar aplicar el mismo patrón a BitacoraViewer y SummariesViewer si también se sienten angostos

---

## Referencias

- [App.svelte](../../ui/src/App.svelte) — Componente principal
- [DocsViewer.svelte](../../ui/src/components/DocsViewer.svelte) — Visualizador de documentación
- [app.css](../../ui/src/app.css) — Estilos globales
