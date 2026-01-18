# Captura de Errores con Trazabilidad — Guía Completa

**Versión**: v0.1+  
**Objetivo**: Documentar el sistema de captura de errores/logs con trazabilidad error → commit → fix.

---

## Resumen Ejecutivo

El sistema de captura de errores permite:

1. **Capturar errores/logs** durante el trabajo diario
2. **Detectar errores repetidos** mediante hash SHA256
3. **Linkear fixes** a errores capturados
4. **Trazar el ciclo completo**: error → commit → fix
5. **Visualizar errores abiertos** en la UI

**Principio rector**: No tomar "último mensaje de terminal" (frágil). Implementar captura explícita con evidencia completa.

---

## Comandos CLI

### `dia E` — Capturar error con título automático (recomendado)

**Sintaxis**:
```bash
dia E ["mensaje de error"] [--repo <path>] [--stdin]
```

**Ejemplos**:

**Con mensaje como argumento** (más rápido):
```bash
dia E "Error al cargar bitácora: HTTP 404" --data-root /ruta/al/monorepo/data --area it
```

**Por pipe**:
```bash
docker-compose up 2>&1 | dia E --data-root /ruta/al/monorepo/data --area it
```

**Qué hace**:
1. Genera título automáticamente (LLM si está configurado, o análisis simple)
2. Lee contenido desde stdin o argumento
3. Calcula hash SHA256 del contenido
4. Busca errores similares anteriores (por palabras clave)
5. Verifica si el error ya existe (mismo hash)
6. Guarda artifact y genera metadatos
7. Registra evento `CaptureCreated` o `CaptureReoccurred`
8. Muestra sugerencias de próximos pasos según el flujo

**Salida mejorada**:
- Muestra errores similares encontrados
- Indica si error repetido tiene fix asociado
- Sugiere acciones siguientes (revisar artifact → fix → commit)

**Parámetros**:
- `mensaje de error` (opcional): mensaje directo como argumento
- `--repo` (optional): path del repo (default: cwd)
- `--stdin` (flag): forzar lectura desde stdin

---

### `dia cap` — Capturar error/log (comando completo)

**Sintaxis**:
```bash
dia cap --kind <error|log> --title "<descripción>" [--auto] [--repo <path>] [--stdin]
```

**Ejemplos**:

**Con título automático**:
```bash
echo "Error message" | dia cap --kind error --auto --data-root /ruta/data --area it
```

**Con título manual**:
```bash
docker-compose up 2>&1 | dia cap --kind error --title "docker up falla" --data-root /ruta/data --area it
```

**Qué hace**:
1. Lee contenido desde stdin (pipe o manual)
2. Si usa `--auto`, genera título automáticamente
3. Calcula hash SHA256 del contenido
4. Verifica si el error ya existe (mismo hash)
5. Busca errores similares (si es error)
6. Guarda artifact en `data/artifacts/captures/YYYY-MM-DD/Sxx/cap_<id>.txt`
7. Genera `.meta.json` con metadatos
8. Registra evento `CaptureCreated` o `CaptureReoccurred`

**Parámetros**:
- `--kind` (required): `error` | `log`
- `--title` (opcional si se usa `--auto`): descripción breve
- `--auto` (flag): generar título automáticamente con LLM/análisis
- `--repo` (optional): path del repo (default: cwd)
- `--stdin` (flag): forzar lectura desde stdin (default: auto-detecta pipe)

**Requisitos**:
- Sesión activa (`dia start` ejecutado previamente)
- Repo Git válido

**Salida (error nuevo)**:
```bash
Título generado: Error al cargar bitácora: HTTP 404
✅ Captura creada: cap_a1b2c3d4e5f6
   Artifact: data/artifacts/captures/2026-01-18/S01/cap_a1b2c3d4e5f6.txt
   Meta: data/artifacts/captures/2026-01-18/S01/cap_a1b2c3d4e5f6.meta.json

   📋 Errores similares encontrados (2):
      - Error al cargar bitácora: HTTP 500 (Sesión S01, 2026-01-17)
      - Error HTTP en bitácora (Sesión S01, 2026-01-16)

   💡 Próximos pasos:
      1. Revisar artifact: data/artifacts/captures/...
      2. Analizar y aplicar fix
      3. Linkear fix: dia fix --title "descripción" --data-root ... --area it
      4. Commit: dia pre-feat --data-root ... --area it
```

**Si el error se repite**:
```bash
⚠️  Error repetido detectado (hash: a1b2c3d4...)
   Original: 2026-01-17T10:30:00 - Error al cargar bitácora: HTTP 404
   Sesión original: S01
   ℹ️  Este error ya fue resuelto anteriormente
   # o
   ⚠️  Este error aún no tiene fix asociado
   💡 Sugerencia: Revisa el fix anterior o aplica uno nuevo con 'dia fix'
```

---

### `dia fix` — Linkear fix a error

**Sintaxis**:
```bash
dia fix --title "<descripción del fix>" [--from <capture_id>] [--repo <path>]
```

**Ejemplos**:

**Linkear al último error sin fix**:
```bash
dia fix --title "corregir variable de entorno faltante" --data-root /ruta/al/monorepo/data --area it
```

**Linkear a un error específico**:
```bash
dia fix --from cap_a1b2c3d4e5f6 --title "fix específico" --data-root /ruta/al/monorepo/data --area it
```

**Qué hace**:
1. Busca el último error sin fix de la sesión actual (o el especificado)
2. Obtiene el commit actual (HEAD) o marca como working tree
3. Genera evento `FixLinked` con referencia al error
4. Si no hay commit, sugiere usar `dia pre-feat`

**Parámetros**:
- `--title` (required): descripción del fix
- `--from` (optional): `capture_id` específico (default: último sin fix)
- `--repo` (optional): path del repo (default: cwd)

**Requisitos**:
- Sesión activa
- Error capturado previamente (con `dia cap`)

**Salida (con commit)**:
```bash
Fix linkeado a error: a1b2c3d4...
Error event_id: evt_01J2QAG7K9M3N5P8Q2R4S6T1U3V
Fix commit: d4c3b2a1
```

**Salida (working tree)**:
```bash
Fix linkeado a error: a1b2c3d4...
Error event_id: evt_01J2QAG7K9M3N5P8Q2R4S6T1U3V
Fix en working tree (aun sin commit)
Ejecuta 'dia pre-feat' para sugerir commit
```

---

## Integración con `dia pre-feat`

Cuando ejecutas `dia pre-feat` y hay un error activo sin fix:

**Comportamiento automático**:
- Detecta el último `CaptureCreated` sin `FixLinked`
- Sugiere mensaje de commit tipo: `fix: <título> [dia] [#sesion Sxx] [#error <hash>]`
- Agrega referencia en `payload.error_ref` del evento `CommitSuggestionIssued`

**Ejemplo de salida**:
```bash
git-commit-cursor -m "🦾 fix: corregir variable de entorno faltante [dia] [#sesion S01] [#error a1b2c3d4]"
```

**Sin error activo**: Comportamiento normal (sugiere según tipo de cambio).

---

## Estructura de Archivos

### Artifacts de capturas

```
data/artifacts/captures/
  YYYY-MM-DD/
    S01/
      cap_a1b2c3d4e5f6.txt          # Contenido del error/log
      cap_a1b2c3d4e5f6.meta.json    # Metadatos
```

### Formato `.meta.json`

```json
{
  "capture_id": "cap_a1b2c3d4e5f6",
  "kind": "error",
  "title": "deploy staging falla",
  "content_hash": "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456",
  "repo": {
    "path": "/path/to/repo",
    "branch": "main",
    "head_sha": "a1b2c3d4"
  },
  "session": {
    "day_id": "2026-01-18",
    "session_id": "S01"
  },
  "timestamp": "2026-01-18T15:15:00-03:00"
}
```

---

## Eventos NDJSON

### `CaptureCreated`

Registrado cuando se captura un error/log nuevo.

**Payload**:
- `kind`: `error` | `log`
- `title`: descripción
- `error_hash`: SHA256 del contenido
- `artifact_ref`: path relativo al artifact

**Repo**: Incluye `head_sha` del commit donde ocurrió el error.

### `CaptureReoccurred`

Registrado cuando se detecta un error repetido (mismo hash).

**Payload**:
- `error_hash`: hash del error repetido
- `original_event_id`: event_id del primer `CaptureCreated`
- `artifact_ref`: path al nuevo artifact
- `title`: descripción

### `FixLinked`

Registrado cuando se linkea un fix a un error.

**Payload**:
- `error_event_id`: referencia al `CaptureCreated`
- `error_hash`: hash del error
- `fix_sha`: SHA del commit del fix (o `null` si working tree)
- `title`: descripción del fix

---

## Trazabilidad Completa

El sistema permite responder estas preguntas:

### ¿Qué commit introdujo el error?

Buscar `CaptureCreated` con `error_hash` → `repo.head_sha`

### ¿Qué commit lo arregló?

Buscar `FixLinked` con `error_event_id` → `payload.fix_sha`

### ¿Reapareció o era nuevo?

Presencia de `CaptureReoccurred` con `original_event_id` → error repetido

### ¿Hay errores sin fix?

Buscar `CaptureCreated` sin `FixLinked` asociado usando `error_event_id` (asociación específica por evento, no por hash).

**Nota importante**: El sistema usa `error_event_id` para asociar fixes a errores específicos, permitiendo que errores con el mismo `error_hash` (errores repetidos) tengan fixes independientes. Esto mejora la precisión de la trazabilidad.

---

## API Endpoints

### `/api/captures/recent/`

Retorna capturas recientes (CaptureCreated y CaptureReoccurred).

**Query params**:
- `limit` (default: 20): número máximo de resultados

**Ejemplo**:
```bash
curl http://localhost:8000/api/captures/recent/?limit=10
```

**Respuesta**:
```json
{
  "captures": [
    {
      "event_id": "evt_...",
      "type": "CaptureCreated",
      "ts": "2026-01-18T15:15:00-03:00",
      "session": {...},
      "payload": {
        "kind": "error",
        "title": "deploy staging falla",
        "error_hash": "...",
        "artifact_ref": "..."
      },
      "links": [...]
    }
  ]
}
```

### `/api/captures/errors/open/`

Retorna lista de errores sin fix (último CaptureCreated sin FixLinked por sesión).

**Lógica de detección**:
- Usa `error_event_id` para asociar `FixLinked` a `CaptureCreated` específicos
- Un error está fijado solo si tiene un `FixLinked` con su `error_event_id` específico
- Esto permite que errores con el mismo `error_hash` (errores repetidos) tengan fixes independientes
- Solo muestra el error más reciente por sesión

**Ejemplo**:
```bash
curl http://localhost:8000/api/captures/errors/open/
```

**Respuesta**:
```json
{
  "errors": [
    {
      "event_id": "evt_...",
      "ts": "2026-01-18T15:15:00-03:00",
      "session": {
        "day_id": "2026-01-18",
        "session_id": "S01"
      },
      "title": "deploy staging falla",
      "error_hash": "...",
      "artifact_ref": "artifacts/captures/2026-01-18/S01/cap_...txt",
      "links": [...]
    }
  ]
}
```

---

## Visualización en UI

### Zona Viva

Muestra sección **"Errores abiertos"** con:
- Título del error
- Sesión y timestamp
- Link al artifact
- Máximo 5 errores (más recientes primero)

### Zona Indeleble

Muestra métrica: **"Errores abiertos: N"** en el card de resumen.

**Auto-refresh incremental**: Actualización silenciosa cada 5 segundos que preserva el estado de la UI (tooltips, scroll). Pausa automáticamente cuando la ventana no está visible. Ver [ALTERNATIVAS_REFRESH.md](../../modules/ui/ALTERNATIVAS_REFRESH.md) para detalles.

---

## Flujo de Trabajo Recomendado

### 1. Error ocurre

```bash
# Opción rápida (recomendado): comando corto con título automático
dia E "descripción del error" --data-root /ruta/data --area it

# O desde pipe
comando_que_falla 2>&1 | dia E --data-root /ruta/data --area it

# Opción completa: con título manual
comando_que_falla 2>&1 | dia cap --kind error --title "descripción" --data-root /ruta/data --area it
```

**El comando automáticamente**:
- Genera título descriptivo
- Busca errores similares anteriores
- Muestra sugerencias de próximos pasos

### 2. Analizar y arreglar

- Revisar artifact: `data/artifacts/captures/YYYY-MM-DD/Sxx/cap_<id>.txt`
- Analizar el error
- **Implementar fix en el código** (editar archivos, corregir el problema)

### 3. Linkear fix al error

**Después de aplicar el fix**, linkearlo al error capturado:

```bash
# Si es el último error sin fix
dia fix --title "descripción del fix" --data-root /ruta/data --area it

# Si hay múltiples errores y quieres linkear uno específico
dia fix --from cap_<id> --title "descripción del fix" --data-root /ruta/data --area it
```

**Importante**: 
- Linkear el fix **después** de haber corregido el código
- Si el error ya fue corregido en un commit anterior, puedes linkearlo usando `--from` con el `capture_id`
- El `capture_id` se encuentra en el artifact: `cap_<id>.txt`

### 4. Checkpoint y commit

```bash
# Checkpoint (detecta automáticamente fixes linkeados)
dia pre-feat --data-root /ruta/data --area it

# Copiar y ejecutar comando sugerido
# Si hay un error con fix linkeado, el mensaje incluirá referencia
git-commit-cursor -m "🦾 fix: descripción del fix [#sesion Sxx]"
```

### 5. Verificar trazabilidad

- Error capturado → `CaptureCreated` (con `error_hash` y `artifact_ref`)
- Fix linkeado → `FixLinked` (con `error_event_id` y `fix_sha`)
- Commit sugerido → `CommitSuggestionIssued` (con `error_ref` si aplica)
- El error desaparece de "errores abiertos" una vez linkeado el fix

---

## Casos de Uso

### Caso 1: Error en deploy

```bash
# Deploy falla
./deploy.sh 2>&1 | dia cap --kind error --title "deploy staging falla" --data-root /ruta/data --area it

# Arreglar problema
# ... editar código ...

# Linkear fix
dia fix --title "corregir variable de entorno" --data-root /ruta/data --area it

# Commit
dia pre-feat --data-root /ruta/data --area it
# Ejecutar comando sugerido
```

### Caso 2: Error repetido

```bash
# Primera vez
echo "Error: connection timeout" | dia cap --kind error --title "timeout" --data-root /ruta/data --area it
# → CaptureCreated

# Segunda vez (mismo contenido)
echo "Error: connection timeout" | dia cap --kind error --title "timeout" --data-root /ruta/data --area it
# → CaptureReoccurred (detecta hash repetido)
```

### Caso 3: Múltiples errores

```bash
# Error 1
error1 2>&1 | dia cap --kind error --title "error 1" --data-root /ruta/data --area it
# → Captura creada: cap_a1b2c3d4e5f6

# Error 2
error2 2>&1 | dia cap --kind error --title "error 2" --data-root /ruta/data --area it
# → Captura creada: cap_f6e5d4c3b2a1

# Arreglar error 1 en el código
# ... editar archivos ...

# Linkear fix al error 1 (usar --from con el capture_id)
dia fix --from cap_a1b2c3d4e5f6 --title "fix error 1" --data-root /ruta/data --area it

# Arreglar error 2 en el código
# ... editar archivos ...

# Linkear fix al error 2
dia fix --from cap_f6e5d4c3b2a1 --title "fix error 2" --data-root /ruta/data --area it

# Checkpoint y commit
dia pre-feat --data-root /ruta/data --area it
# Ejecutar comando sugerido
```

### Caso 4: Error ya corregido (linkear fix retroactivo)

Si encuentras un error que ya fue corregido en un commit anterior:

```bash
# 1. Capturar el error (si no está capturado)
dia E "Error ya corregido" --data-root /ruta/data --area it
# → Anotar el capture_id: cap_<id>

# 2. Linkear el fix al error usando el commit que lo corrigió
dia fix --from cap_<id> --title "Fix aplicado en commit anterior" --data-root /ruta/data --area it
# → Esto linkea el commit actual (HEAD) al error

# Nota: Si el fix está en un commit anterior, puedes hacer checkout a ese commit antes de linkear
```

---

## Preguntas Frecuentes

### ¿Puedo capturar logs que no son errores?

Sí, usa `--kind log`:
```bash
comando 2>&1 | dia cap --kind log --title "log de inicio" --data-root /ruta/data --area it
```

### ¿Qué pasa si no hay sesión activa?

`dia cap` y `dia fix` requieren sesión activa. Ejecuta `dia start` primero.

### ¿Cómo veo todos los errores capturados?

Usa la API:
```bash
curl http://localhost:8000/api/captures/recent/?limit=50
```

### ¿Cómo veo solo errores sin fix?

Usa la API:
```bash
curl http://localhost:8000/api/captures/errors/open/
```

O revisa la UI (zona viva, sección "Errores abiertos").

### ¿El hash detecta errores similares o solo idénticos?

Solo idénticos. El hash SHA256 es del contenido exacto. Errores similares pero no idénticos generan hashes diferentes.

### ¿Puedo linkear un fix a un error de otra sesión?

Sí, usando `--from <capture_id>` con el ID específico del error.

---

## Mejoras Recientes

### v0.1+ (2026-01-17): Precisión en detección de errores fijados

**Problema anterior**: El sistema usaba solo `error_hash` para determinar si un error estaba fijado, lo que causaba que todos los `CaptureCreated` con el mismo hash se marcaran como fijados cuando solo uno tenía un `FixLinked` asociado.

**Solución implementada**: 
- La lógica ahora usa `error_event_id` para asociar `FixLinked` a `CaptureCreated` específicos
- Un error está fijado solo si tiene un `FixLinked` con su `error_event_id` específico
- Esto permite que errores con el mismo `error_hash` (errores repetidos) tengan fixes independientes
- Mejora la precisión de la trazabilidad y evita falsos positivos en errores abiertos

**Archivos modificados**:
- `server/api/views.py`: Función `errors_open()` actualizada
- `cli/dia_cli/utils.py`: Función `find_last_unfixed_capture()` actualizada

---

## Próximos Pasos

- Integración con `close-day`: incluir métricas de errores capturados vs resueltos
- Análisis de patrones: detectar errores que reaparecen frecuentemente
- Sugerencias automáticas: proponer fixes basados en errores similares del historial

---

**Última actualización**: 2026-01-17  
**Versión del sistema**: v0.1+
