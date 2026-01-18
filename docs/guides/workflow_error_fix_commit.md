# Workflow Error → Fix → Commit

**Versión**: v0.1.1  
**Objetivo**: Documentar el flujo completo de captura de errores, linkeo de fixes y commits con trazabilidad completa.

---

## Resumen Ejecutivo

El workflow E→Fix→Commit permite:

1. **Capturar errores** de forma estructurada
2. **Linkear fixes** a errores específicos
3. **Trazar commits** que resuelven los errores
4. **Visualizar la cadena completa** en la UI

**Principio rector**: Trazabilidad explícita y auditable. Cada paso queda registrado en eventos NDJSON.

---

## Flujo Completo

### 1. Capturar error

```bash
dia E "mensaje de error" --data-root /ruta/data --area it
```

O desde pipe:

```bash
comando_que_falla 2>&1 | dia E --data-root /ruta/data --area it
```

**Qué hace**:
- Genera título automáticamente (LLM si está configurado, o análisis simple)
- Calcula hash SHA256 del contenido
- Busca errores similares anteriores
- Guarda artifact en `data/artifacts/captures/YYYY-MM-DD/Sxx/cap_<id>.txt`
- Registra evento `CaptureCreated` con `capture_id` y `error_hash`

**Salida**:
```
✅ Captura creada: cap_a1b2c3d4e5f6
   Artifact: data/artifacts/captures/2026-01-18/S01/cap_a1b2c3d4e5f6.txt
   Fix ID: (pendiente)
```

---

### 2. Implementar fix en código

**Importante**: El sistema NO implementa el fix. Tú debes:

- Revisar el artifact del error
- Analizar la causa
- Editar los archivos necesarios
- Verificar que el fix funciona

---

### 3. Linkear fix al error

**Después de aplicar el fix**, linkearlo al error capturado:

```bash
# Si es el último error sin fix
dia fix --title "descripción del fix" --data-root /ruta/data --area it

# Si hay múltiples errores y quieres linkear uno específico
dia fix --from cap_<id> --title "descripción del fix" --data-root /ruta/data --area it
```

**Qué hace**:
- Busca el error (último sin fix o el especificado)
- Genera `fix_id` único (ej: `fix_abc123`)
- Registra evento `FixLinked` con:
  - `fix_id`: identificador único del fix
  - `error_event_id`: referencia al error original
  - `fix_sha`: SHA del commit actual (si existe) o `null` si está en working tree
  - `title`: descripción del fix

**Salida**:
```
Fix linkeado a error: a1b2c3d4...
Fix ID: fix_abc123
Error event_id: evt_01J2QAG7K9M3N5P8Q2R4S6T1U3V
Fix en working tree (aun sin commit)
Ejecuta 'dia pre-feat' para sugerir commit
Luego usa 'dia fix-commit --fix fix_abc123 --last' para linkear el commit
```

---

### 4. Checkpoint y commit

```bash
# Checkpoint (detecta automáticamente fixes linkeados)
dia pre-feat --data-root /ruta/data --area it
```

Si hay un error con fix linkeado, el mensaje sugerido incluirá referencia:

```bash
git-commit-cursor -m "🦾 fix: descripción del fix [#sesion S01]"
```

**Luego hacer commit manual**:

```bash
git add <archivos_del_fix>
git commit -m "🦾 fix: descripción del fix [#sesion S01]"
```

---

### 5. Linkear fix a commit

**Después del commit**, linkear el fix al commit SHA:

```bash
# Usar HEAD (más común)
dia fix-commit --fix fix_abc123 --last --data-root /ruta/data --area it

# O especificar SHA explícito
dia fix-commit --fix fix_abc123 --commit abc123def456 --data-root /ruta/data --area it
```

**Qué hace**:
- Busca el `FixLinked` por `fix_id`
- Valida que el commit existe en el repo
- Registra evento `FixCommitted` con:
  - `fix_event_id`: referencia al `FixLinked`
  - `commit_sha`: SHA del commit
  - `error_event_id`: referencia al error original

**Salida**:
```
Fix fix_abc123 linkeado al commit abc123def456
Error event_id: evt_01J2QAG7K9M3N5P8Q2R4S6T1U3V
Commit SHA: abc123def456
```

---

## Reglas de Staging

### Qué NO commitea

El sistema está configurado para **no commitea** automáticamente:

- `data/` - datos de runtime (fuera del repo con Opción B)
- `.dia/` - data local por proyecto (ignorado)
- `artifacts/` - artifacts generados
- `__pycache__/`, `*.pyc` - archivos compilados de Python
- `node_modules/` - dependencias de Node.js

**Regla práctica**: Solo commitea código fuente, documentación (`docs/`), y configuración del proyecto.

### Cómo mantener commits limpios

1. **Revisar `git status`** antes de commitear
2. **Usar `git add` selectivo** (no `git add .`)
3. **Verificar que no se incluyen** archivos de `data/` o `.dia/`
4. **Usar `dia pre-feat`** para obtener mensaje sugerido con formato correcto

---

## Ejemplos Prácticos

### Ejemplo 1: Error en deploy

```bash
# 1. Capturar error
./deploy.sh 2>&1 | dia E --data-root ~/.local/share/dia --area it
# → cap_a1b2c3d4e5f6

# 2. Arreglar problema (editar código manualmente)
vim config/deploy.yml  # corregir variable de entorno

# 3. Linkear fix
dia fix --from cap_a1b2c3d4e5f6 --title "corregir variable de entorno faltante" --data-root ~/.local/share/dia --area it
# → fix_abc123

# 4. Checkpoint y commit
dia pre-feat --data-root ~/.local/share/dia --area it
# → sugiere: git-commit-cursor -m "🦾 fix: corregir variable de entorno faltante [#sesion S01]"

git add config/deploy.yml
git commit -m "🦾 fix: corregir variable de entorno faltante [#sesion S01]"

# 5. Linkear commit
dia fix-commit --fix fix_abc123 --last --data-root ~/.local/share/dia --area it
```

### Ejemplo 2: Múltiples errores

```bash
# Error 1
error1 2>&1 | dia E --data-root ~/.local/share/dia --area it
# → cap_a1b2c3d4e5f6

# Error 2
error2 2>&1 | dia E --data-root ~/.local/share/dia --area it
# → cap_b2c3d4e5f6a7

# Arreglar ambos
# ... editar código ...

# Linkear fix 1
dia fix --from cap_a1b2c3d4e5f6 --title "fix error 1" --data-root ~/.local/share/dia --area it
# → fix_abc123

# Linkear fix 2
dia fix --from cap_b2c3d4e5f6a7 --title "fix error 2" --data-root ~/.local/share/dia --area it
# → fix_def456

# Commits separados
git add file1.py
git commit -m "🦾 fix: fix error 1 [#sesion S01]"
dia fix-commit --fix fix_abc123 --last --data-root ~/.local/share/dia --area it

git add file2.py
git commit -m "🦾 fix: fix error 2 [#sesion S01]"
dia fix-commit --fix fix_def456 --last --data-root ~/.local/share/dia --area it
```

---

## Visualización en UI

### Zona Viva - Cadena Error/Fix/Commit

La UI muestra una barra de cadena que visualiza:

- **Error**: último error capturado sin fix
- **Fix**: fix linkeado (si existe) con `fix_id`
- **Commit**: commit linkeado (si existe) con `commit_sha`

**Botones de guía** (no ejecutan, solo muestran comandos):
- "Crear fix" → muestra comando `dia fix --from cap_<id> ...`
- "Link commit" → muestra comando `dia fix-commit --fix fix_<id> --last`

---

## Trazabilidad Completa

La cadena completa queda registrada en eventos NDJSON:

1. **Error capturado** → `CaptureCreated` (con `error_hash` y `artifact_ref`)
2. **Fix linkeado** → `FixLinked` (con `fix_id`, `error_event_id`, `fix_sha`)
3. **Commit linkeado** → `FixCommitted` (con `fix_event_id`, `commit_sha`, `error_event_id`)

**Preguntas que puedes responder**:
- ¿Qué commit introdujo el error? → `repo.head_sha` del `CaptureCreated`
- ¿Qué commit lo arregló? → `commit_sha` del `FixCommitted`
- ¿El error reapareció? → Presencia de `CaptureReoccurred`
- ¿Hay fixes sin commit? → `FixLinked` sin `FixCommitted` asociado

---

## Troubleshooting

### "No hay errores sin fix en esta sesion"

**Causa**: Todos los errores capturados ya tienen fixes linkeados.

**Solución**: Usa `--from cap_<id>` para linkear un error específico, o captura un nuevo error.

### "Fix <fix_id> no encontrado"

**Causa**: El `fix_id` no existe o está mal escrito.

**Solución**: Verifica el `fix_id` en la salida de `dia fix`, o busca en los eventos.

### "Commit <sha> no encontrado en el repo"

**Causa**: El SHA no existe en el repo actual o está mal escrito.

**Solución**: Verifica el SHA con `git log`, o usa `--last` para usar HEAD automáticamente.

### "Fix <fix_id> ya está linkeado al commit <sha>"

**Causa**: El fix ya tiene un commit asociado.

**Solución**: Esto es normal. Si necesitas cambiar el commit, primero debes eliminar el `FixCommitted` anterior (no implementado en v0.1.1).

---

## Mejores Prácticas

1. **Captura errores inmediatamente**: No esperes a "arreglarlo después"
2. **Linkea fixes después de corregir**: No antes de implementar el fix
3. **Usa `--last` para commits**: Más rápido que copiar SHA manualmente
4. **Revisa la cadena en UI**: Verifica que todo esté linkeado correctamente
5. **Mantén commits limpios**: No incluyas archivos de `data/` o `.dia/`

---

## Próximos Pasos

- Ver [CAPTURA_ERRORES.md](../manual/CAPTURA_ERRORES.md) para detalles de captura
- Ver [dia-desarrollo.md](./dia-desarrollo.md) para workflow general de desarrollo
- Ver [sesiones-multiples.md](./sesiones-multiples.md) para trabajar con múltiples repos
