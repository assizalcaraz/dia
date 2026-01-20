# BitacoraEditor

**Ubicación**: `ui/src/components/BitacoraEditor.svelte`  
**Versión**: v0.1

Componente para editar las secciones editables (1 y 2) de la bitácora diaria. Permite edición en tiempo real con auto-guardado.

---

## Propósito

Permite editar las secciones manuales de la bitácora diaria:
- **Sección 1**: Intención del día (manual, editable)
- **Sección 2**: Notas humanas (manual, editable)
- **Sección 3**: Registro automático (read-only, no editable)

---

## Props

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `apiBase` | `string` | `"/api"` | Base URL de la API |
| `dayId` | `string \| null` | `null` | ID del día (formato `YYYY-MM-DD`) |

---

## Funcionalidad

### Edición de Secciones Manuales

- **Separación automática**: Detecta y separa secciones editables (1 y 2) de la sección automática (3)
- **Editor de texto**: Textarea para editar contenido de secciones 1 y 2
- **Visualización read-only**: Muestra la sección 3 (automática) usando `MarkdownRenderer`

### Auto-guardado

- **Delay de 2 segundos**: Guarda automáticamente después de 2 segundos sin escribir
- **Indicador de guardado**: Muestra "Guardando..." mientras se guarda
- **Confirmación visual**: Muestra "Guardado" con timestamp después de guardar exitosamente
- **Manejo de errores**: Muestra mensaje de error si falla el guardado

### Carga de Datos

- **Carga automática**: Carga la bitácora al montar el componente o cuando cambia `dayId`
- **Parsing inteligente**: Separa contenido editable de contenido automático usando el separador `---\n\n## 3. Registro automático (NO EDITAR)`

---

## Integración con API

### Endpoints utilizados

- `GET /api/jornada/{day_id}/` — Obtiene contenido de la bitácora del día
- `PUT /api/jornada/{day_id}/` — Guarda las secciones editables de la bitácora

---

## Estados

- `humanSections`: Contenido de secciones 1 y 2 (editables)
- `autoSection`: Contenido de sección 3 (read-only)
- `isEditing`: Indica si el usuario está editando
- `isSaving`: Indica si se está guardando
- `lastSaved`: Timestamp del último guardado exitoso
- `error`: Mensaje de error si ocurre algún problema
- `saveTimeout`: Referencia al timeout de auto-guardado

---

## Comportamiento

- **Al montar**: Carga la bitácora del día especificado
- **Al escribir**: Inicia timeout de 2 segundos para auto-guardado
- **Al guardar**: Envía solo las secciones editables (1 y 2) a la API
- **Al cambiar `dayId`**: Recarga la bitácora del nuevo día

---

## Dependencias

- `MarkdownRenderer`: Para renderizar la sección automática (read-only)

---

## Ejemplo de uso

```svelte
<BitacoraEditor apiBase="/api" dayId="2026-01-19" />
```

---

## Referencias

- [BitacoraViewer](./BitacoraViewer.md) — Componente de visualización de bitácoras
- [MarkdownRenderer](./MarkdownRenderer.md) — Componente de renderizado de markdown
- [Documentación de API](../../modules/api/endpoints.md#jornada) — Endpoint de bitácoras
