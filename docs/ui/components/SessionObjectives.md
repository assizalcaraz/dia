# SessionObjectives

**Ubicación**: `ui/src/components/SessionObjectives.svelte`  
**Versión**: v0.1

Componente simple para mostrar los objetivos de una sesión activa: Intent (objetivo) y DoD (Definition of Done).

---

## Propósito

Muestra de forma clara y concisa:
- **Intent**: Objetivo de la sesión (1 frase)
- **DoD**: Definition of Done (criterios de completitud)

---

## Props

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `session` | `object \| null` | `null` | Objeto de sesión con propiedades `session_id`, `intent`, `dod` |

---

## Estructura de Sesión

```typescript
{
  session_id: string,  // Ej: "S01"
  intent?: string,     // Objetivo de la sesión
  dod?: string         // Definition of Done
}
```

---

## Funcionalidad

### Visualización

- **Card con borde**: Muestra información en un card con borde destacado
- **Badge de sesión**: Muestra el ID de la sesión (ej: "S01")
- **Valores por defecto**: Muestra "No especificado" si falta `intent` o `dod`

### Estado Vacío

- **Sin sesión**: Muestra mensaje "No hay sesión activa" cuando `session` es `null`

---

## Estilos

El componente usa variables CSS del sistema de diseño:
- `--color-border-strong`: Borde destacado del card
- `--color-surface`: Fondo del card
- `--spacing-*`: Espaciado consistente
- `--radius-md`: Bordes redondeados
- `--shadow-sm`: Sombra sutil en hover

---

## Dependencias

Este componente es usado por:
- `App`: Se muestra en el tab "Sesión" y "Objetivos" de la zona viva

---

## Ejemplo de uso

```svelte
<SessionObjectives 
  session={{
    session_id: "S01",
    intent: "Implementar sistema de gestión de datos",
    dod: "Documentación completa y tests pasando"
  }}
/>
```

---

## Referencias

- [App](../App.md) — Componente principal que usa este componente
- [Documentación de sesiones](../../modules/cli/sessions.md) — Gestión de sesiones en CLI
