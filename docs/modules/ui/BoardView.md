# BoardView

**Ubicación**: `ui/src/components/BoardView.svelte`  
**Versión**: v0.2.0 (Fase 1)  
**Estado**: Implementado

Componente Svelte fullscreen que implementa el Feature Board, un canvas interactivo para organizar y visualizar elementos (notas, tareas, sesiones, errores) en un espacio de trabajo infinito.

---

## Props

- `boardId` (string, requerido): Identificador del board. Usa `session_id` si hay sesión activa, o `day_id` si no.
- `onClose` (function, requerido): Callback que se ejecuta al cerrar el board

---

## Funcionalidad

### Fase 1 (Implementado)

1. **Vista fullscreen**: Overlay que ocupa toda la pantalla con z-index 1000
2. **Canvas básico**: Área de trabajo con sistema de coordenadas y viewport
3. **Renderizado de elementos**: Muestra elementos del board usando `BoardElement`
4. **Persistencia automática**: Guarda y carga estado desde localStorage
5. **Sistema de coordenadas**: Viewport con posición (x, y) y zoom

### Próximas Fases

- **Fase 2**: Drag & drop, creación de notas, zoom/pan interactivo
- **Fase 3**: Sistema de rutinas para procesar elementos seleccionados
- **Fase 4**: Integración con API para cargar sesiones/errores
- **Fase 5**: Conexiones visuales entre elementos
- **Fase 6**: Rutinas avanzadas y personalización

---

## Dependencias

### Componentes

- `BoardElement`: Renderiza elementos individuales del board

### Stores

- `boardStore.js`: 
  - `boardState`: Estado del board (elementos, conexiones, viewport)
  - `viewport`: Posición y zoom del viewport
  - `initializeBoardStore(boardId)`: Inicializa y carga estado
  - `cleanupBoardStore()`: Limpia suscripciones

### Tipos

- `types/board.ts`: Definiciones TypeScript (referencia, no importado directamente)

---

## Integración con App.svelte

El board se integra en `App.svelte` mediante:

```svelte
{#if boardOpen}
  <BoardView boardId={boardId} onClose={closeBoard} />
{/if}
```

Donde:
- `boardOpen`: Variable reactiva que controla visibilidad
- `boardId`: Calculado como `currentSession?.session_id || today`
- `closeBoard()`: Función que establece `boardOpen = false`

---

## Persistencia

### localStorage

El estado se guarda automáticamente en localStorage con la clave:
```
board_{boardId}
```

Estructura del estado guardado:
```json
{
  "id": "S02",
  "elements": [],
  "connections": [],
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "lastModified": "2026-01-17T21:30:00.000Z"
}
```

### Auto-guardado

El store se suscribe automáticamente a cambios en `boardState` y guarda en localStorage cada vez que cambia.

---

## Estados

- `currentViewport`: Viewport actual (derivado de store `$viewport`)
- `currentBoardState`: Estado del board actual (derivado de store `$boardState`)

---

## Comportamiento

1. **Al montar**: 
   - Inicializa el store con `initializeBoardStore(boardId)`
   - Carga estado desde localStorage (o crea board vacío si no existe)

2. **Al desmontar**:
   - Limpia suscripciones con `cleanupBoardStore()`

3. **Renderizado**:
   - Si hay elementos, los renderiza usando `BoardElement`
   - Si no hay elementos, muestra mensaje "Board vacío"

---

## Estilos

### Clases principales

- `.board-fullscreen`: Contenedor fullscreen con posición fixed
- `.board-header`: Header con título y botón cerrar
- `.board-canvas`: Canvas con grid de fondo y sistema de coordenadas
- `.board-empty`: Mensaje cuando el board está vacío

### Variables CSS utilizadas

- `--color-bg`, `--color-surface`, `--color-border`, `--color-border-strong`
- `--color-text`, `--color-text-muted`
- `--spacing-*`, `--radius-*`, `--shadow-*`, `--transition`

---

## Ejemplo de Uso

```svelte
<script>
  import BoardView from './components/BoardView.svelte';
  
  let boardOpen = false;
  let boardId = 'S02';
  
  function closeBoard() {
    boardOpen = false;
  }
</script>

<button on:click={() => boardOpen = true}>Abrir Board</button>

{#if boardOpen}
  <BoardView boardId={boardId} onClose={closeBoard} />
{/if}
```

---

## Limitaciones Actuales (Fase 1)

- ❌ No hay drag & drop (elementos no son arrastrables)
- ❌ No hay creación de elementos desde el board
- ❌ No hay zoom/pan interactivo
- ❌ No hay sistema de rutinas
- ❌ No hay integración con API (solo localStorage)
- ❌ No hay conexiones visuales entre elementos

---

## Referencias

- [PLAN_ACTUALIZACION_ZONA_VIVA.md](./PLAN_ACTUALIZACION_ZONA_VIVA.md) - Plan completo del Feature Board
- [SISTEMA_RUTINAS_BOARD.md](./SISTEMA_RUTINAS_BOARD.md) - Especificación del sistema de rutinas
- [RESUMEN_PLAN_BOARD.md](./RESUMEN_PLAN_BOARD.md) - Resumen ejecutivo

---

**Última actualización**: 2026-01-17
