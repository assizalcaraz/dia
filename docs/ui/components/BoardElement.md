# BoardElement

**Ubicación**: `ui/src/components/BoardElement.svelte`  
**Versión**: v0.2

Componente para renderizar elementos individuales del Feature Board. Cada elemento se posiciona y escala según el viewport del canvas.

---

## Propósito

Renderiza un elemento del board con:
- Posición y tamaño transformados según zoom y pan del viewport
- Icono según tipo de elemento
- Título y contenido
- Soporte para imágenes

---

## Props

| Prop | Tipo | Descripción |
|------|------|-------------|
| `element` | `object` | Objeto del elemento con propiedades: `type`, `position`, `size`, `content`, `zIndex` |
| `viewport` | `object` | Objeto del viewport con propiedades: `x`, `y`, `zoom` |

---

## Estructura del Elemento

```typescript
{
  type: 'note' | 'task' | 'session' | 'error' | 'custom',
  position: { x: number, y: number },
  size: { width: number, height: number },
  content: {
    title: string,
    data?: {
      imageData?: string  // Base64 image data
    }
  },
  zIndex?: number
}
```

---

## Funcionalidad

### Transformación de Coordenadas

- **Posición transformada**: Calcula posición en pantalla según zoom y pan del viewport
- **Tamaño transformado**: Escala el tamaño del elemento según el zoom
- **Z-index**: Respeta el z-index del elemento para orden de renderizado

### Iconos por Tipo

| Tipo | Icono |
|------|-------|
| `note` | 📝 |
| `task` | ✓ |
| `session` | 📅 |
| `error` | ⚠️ |
| `custom` | 📦 |

### Soporte de Imágenes

- **Detección automática**: Verifica si el elemento tiene `imageData` en su contenido
- **Renderizado condicional**: Muestra imagen solo si existe `imageData`

---

## Estilos

El componente usa clases CSS modulares:
- `.board-element`: Contenedor principal
- `.board-element--{type}`: Clase específica por tipo
- `.board-element__header`: Encabezado con icono y título
- `.board-element__image`: Contenedor de imagen (si existe)

---

## Dependencias

Este componente es usado por:
- `BoardView`: Renderiza múltiples elementos del board

---

## Ejemplo de uso

```svelte
<BoardElement 
  element={{
    type: 'note',
    position: { x: 100, y: 200 },
    size: { width: 150, height: 80 },
    content: { title: 'Nota importante' },
    zIndex: 1
  }}
  viewport={{ x: 0, y: 0, zoom: 1.0 }}
/>
```

---

## Referencias

- [BoardView](../BoardView.md) — Componente principal del Feature Board
- [Documentación de Feature Board](../design/) — Diseño y arquitectura del board
