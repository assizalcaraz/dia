# ErrorFixCommitChain

**Ubicación**: `ui/src/components/ErrorFixCommitChain.svelte`  
**Versión**: v0.1.1

Componente para visualizar la cadena Error→Fix→Commit más reciente. Muestra información de cada eslabón y comandos sugeridos para continuar el workflow.

---

## Propósito

Visualiza la última cadena abierta de Error/Fix/Commit para:
- Ver el estado actual del workflow
- Entender qué error se está trabajando
- Ver qué fix se ha aplicado
- Verificar si hay commit asociado
- Obtener comandos sugeridos para continuar

---

## Props

| Prop | Tipo | Default | Descripción |
|------|------|---------|-------------|
| `apiBase` | `string` | `"/api"` | Base URL de la API |

---

## Funcionalidad

### Visualización de Cadena

Muestra tres secciones principales:

1. **Error** (si existe):
   - Título del error
   - Sesión y fecha
   - Referencia al artifact
   - Hash del error
   - Botón para copiar información

2. **Fix** (si existe):
   - Título del fix
   - Sesión y fecha
   - Referencia al error asociado
   - Hash del fix
   - Comando sugerido para linkear commit

3. **Commit** (si existe):
   - Hash del commit
   - Mensaje del commit
   - Fecha del commit
   - Referencia al fix asociado

### Comandos Sugeridos

- **Si hay error pero no fix**: Muestra comando `dia fix --from cap_<id>`
- **Si hay fix pero no commit**: Muestra comando `dia fix-commit --fix fix_<id>`
- **Botones de copiar**: Permite copiar comandos al portapapeles

### Estados Vacíos

- **Sin cadena**: Muestra mensaje informativo cuando no hay cadena abierta
- **Solo error**: Indica que se puede crear un fix
- **Error + Fix**: Indica que se puede linkear un commit

---

## Integración con API

### Endpoints utilizados

- `GET /api/chain/latest/` — Obtiene la última cadena Error→Fix→Commit

---

## Estados

- `chain`: Objeto con propiedades `error`, `fix`, `commit` (pueden ser `null`)
- `loading`: Indica si se está cargando la cadena
- `error`: Mensaje de error si falla la carga

---

## Comportamiento

- **Al montar**: Carga la última cadena desde la API
- **Copia de comandos**: Usa `navigator.clipboard` para copiar al portapapeles
- **Formato de comandos**: Genera comandos con IDs reales cuando están disponibles

---

## Funciones auxiliares

- `getFixCommand()`: Genera comando `dia fix` con el ID del error
- `getCommitCommand()`: Genera comando `dia fix-commit` con el ID del fix
- `copyToClipboard(text)`: Copia texto al portapapeles

---

## Ejemplo de uso

```svelte
<ErrorFixCommitChain apiBase="/api" />
```

---

## Referencias

- [Workflow Error→Fix→Commit](../../guides/workflow_error_fix_commit.md) — Guía completa del workflow
- [Documentación de API](../../modules/api/endpoints.md#chain) — Endpoint de cadenas
- [App](../App.md) — Componente principal que usa este componente
