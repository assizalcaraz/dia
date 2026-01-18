# Guía: Scopes de Documentación

Esta guía define los **scopes de documentación** para evitar malinterpretar qué documentación actualizar cuando se realizan cambios en el código.

---

## Propósito

Cuando se realizan cambios en el código, es importante actualizar la documentación correspondiente, pero **solo la documentación relevante**. Los scopes ayudan a:

- Identificar qué documentación actualizar según el tipo de cambio
- Evitar actualizar documentación no relacionada
- Mantener consistencia en las actualizaciones

---

## Scopes Definidos

### 1. `cli_commands` — Comandos CLI

**Descripción**: Documentación de comandos CLI y su uso.

**Archivos incluidos**:
- `docs/guides/dia-*.md` (guías de comandos específicos)
- `docs/manual/CAPTURA_ERRORES.md` (manual de captura)
- `docs/modules/cli/*.md` (documentación de módulos CLI)

**Cuándo actualizar**:
- ✅ Cambios en `cli/dia_cli/*.py`
- ✅ Nuevos comandos CLI
- ✅ Cambios en argumentos de comandos
- ✅ Cambios en comportamiento de comandos
- ✅ Nuevas opciones o flags

**Ejemplo**:
```bash
# Cambio: Agregar flag --auto a dia cap
# Actualizar: docs/manual/CAPTURA_ERRORES.md, docs/guides/dia-cap.md
```

---

### 2. `ui_components` — Componentes UI

**Descripción**: Documentación de componentes Svelte y UI.

**Archivos incluidos**:
- `docs/modules/components/*.md` (documentación de componentes)
- `docs/modules/ui/*.md` (documentación de UI)

**Cuándo actualizar**:
- ✅ Cambios en `ui/src/components/*.svelte`
- ✅ Nuevos componentes
- ✅ Cambios en props de componentes
- ✅ Cambios en comportamiento de componentes
- ✅ Nuevas funcionalidades visuales

**Ejemplo**:
```bash
# Cambio: Agregar prop onClose a BoardView
# Actualizar: docs/modules/components/BoardView.md
```

---

### 3. `api_endpoints` — API

**Descripción**: Documentación de endpoints y estructura de respuestas.

**Archivos incluidos**:
- `docs/modules/api/*.md` (documentación de API)
- `docs/guides/api-*.md` (guías de API)

**Cuándo actualizar**:
- ✅ Cambios en `server/api/*.py`
- ✅ Nuevos endpoints
- ✅ Cambios en estructura de respuestas
- ✅ Cambios en parámetros de endpoints
- ✅ Nuevos códigos de estado HTTP

**Ejemplo**:
```bash
# Cambio: Agregar endpoint GET /api/sessions/current/
# Actualizar: docs/modules/api/views.md, docs/guides/api-sessions.md
```

---

### 4. `workflows` — Flujos de Trabajo

**Descripción**: Documentación de procesos y flujos de trabajo.

**Archivos incluidos**:
- `docs/guides/*.md` (guías generales)
- `docs/README.md` (índice principal)

**Cuándo actualizar**:
- ✅ Cambios en flujos documentados
- ✅ Nuevos workflows
- ✅ Actualizaciones de procesos
- ✅ Cambios en recomendaciones de uso

**Ejemplo**:
```bash
# Cambio: Nuevo flujo de captura de errores con dia E
# Actualizar: docs/guides/dia-desarrollo.md, docs/README.md
```

---

### 5. `architecture` — Arquitectura y Diseño

**Descripción**: Documentación de arquitectura, diseño y estado del proyecto.

**Archivos incluidos**:
- `docs/overview/*.md` (vistas generales)
- `docs/specs/*.md` (especificaciones)
- `docs/RESUMEN_DISENO_DIA.md` (resumen de diseño)
- `docs/ESTADO_ACTUAL.md` (estado actual)

**Cuándo actualizar**:
- ✅ Cambios arquitectónicos significativos
- ✅ Nuevas decisiones de diseño
- ✅ Actualizaciones de estado del proyecto
- ✅ Cambios en principios o filosofía

**Ejemplo**:
```bash
# Cambio: Nueva decisión de usar Svelte stores para estado
# Actualizar: docs/overview/ESTADO_ACTUAL.md, docs/RESUMEN_DISENO_DIA.md
```

---

## Uso en Desarrollo

### Proceso Recomendado

1. **Identificar el scope**: Determinar qué scope(s) aplican según el cambio realizado
2. **Revisar triggers**: Verificar si el cambio activa algún trigger del scope
3. **Actualizar documentación**: Actualizar solo los archivos del scope relevante
4. **Commit separado**: Hacer commit de documentación con scope claro

### Ejemplo de Workflow

```bash
# 1. Cambio en código
# Editar: cli/dia_cli/main.py (agregar flag --auto)

# 2. Identificar scope
# Scope: cli_commands
# Archivos a actualizar:
#   - docs/manual/CAPTURA_ERRORES.md
#   - docs/guides/dia-cap.md (si existe)

# 3. Actualizar documentación
# Editar archivos del scope

# 4. Commits
git add cli/dia_cli/main.py
git commit -m "feat: agregar flag --auto a dia cap"

git add docs/manual/CAPTURA_ERRORES.md docs/guides/dia-cap.md
git commit -m "docs(cli_commands): actualizar documentación de dia cap --auto"
```

---

## Reglas en `rules.json`

Los scopes están definidos en `data/rules.json` bajo `documentation_scopes`:

```json
{
  "documentation_scopes": {
    "cli_commands": { ... },
    "ui_components": { ... },
    "api_endpoints": { ... },
    "workflows": { ... },
    "architecture": { ... }
  }
}
```

---

## Notas Importantes

- **No actualizar documentación no relacionada**: Si cambias un comando CLI, no actualices documentación de UI
- **Scopes pueden solaparse**: Un cambio puede afectar múltiples scopes (ej: nuevo comando que afecta workflow)
- **Priorizar relevancia**: Actualizar solo si el cambio es significativo para el usuario/desarrollador
- **Mantener consistencia**: Usar el mismo formato y estilo en todas las actualizaciones

---

## Preguntas Frecuentes

**¿Qué pasa si un cambio afecta múltiples scopes?**
- Actualiza todos los scopes relevantes, pero en commits separados si es posible

**¿Debo actualizar documentación para cambios menores?**
- Solo si el cambio afecta el comportamiento visible o la API pública

**¿Cómo sé qué archivos actualizar exactamente?**
- Revisa la lista de `paths` en el scope correspondiente en `rules.json`
