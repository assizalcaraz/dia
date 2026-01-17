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

### `dia cap` — Capturar error/log

**Sintaxis**:
```bash
dia cap --kind <error|log> --title "<descripción>" [--repo <path>] [--stdin]
```

**Ejemplos**:

**Por pipe** (cuando un comando falla):
```bash
docker-compose up 2>&1 | dia cap --kind error --title "docker up falla" --data-root /ruta/al/monorepo/data --area it
```

**Pegado manual**:
```bash
dia cap --kind error --title "deploy staging" --stdin --data-root /ruta/al/monorepo/data --area it
# Pegar contenido del error, luego Ctrl-D
```

**Qué hace**:
1. Lee contenido desde stdin (pipe o manual)
2. Calcula hash SHA256 del contenido
3. Verifica si el error ya existe (mismo hash)
4. Guarda artifact en `data/artifacts/captures/YYYY-MM-DD/Sxx/cap_<id>.txt`
5. Genera `.meta.json` con metadatos
6. Registra evento `CaptureCreated` o `CaptureReoccurred`

**Parámetros**:
- `--kind` (required): `error` | `log`
- `--title` (required): descripción breve
- `--repo` (optional): path del repo (default: cwd)
- `--stdin` (flag): forzar lectura desde stdin (default: auto-detecta pipe)

**Requisitos**:
- Sesión activa (`dia start` ejecutado previamente)
- Repo Git válido

**Salida**:
```bash
Captura creada: cap_a1b2c3d4e5f6
Artifact: data/artifacts/captures/2026-01-18/S01/cap_a1b2c3d4e5f6.txt
Meta: data/artifacts/captures/2026-01-18/S01/cap_a1b2c3d4e5f6.meta.json
```

**Si el error se repite**:
```bash
Error repetido detectado (hash: a1b2c3d4...)
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

Buscar `CaptureCreated` sin `FixLinked` asociado (mismo `error_hash` o `error_event_id`)

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

**Auto-refresh**: Cada 5 segundos.

---

## Flujo de Trabajo Recomendado

### 1. Error ocurre

```bash
# Capturar error
comando_que_falla 2>&1 | dia cap --kind error --title "descripción" --data-root /ruta/data --area it
```

### 2. Analizar y arreglar

- Revisar artifact: `data/artifacts/captures/YYYY-MM-DD/Sxx/cap_<id>.txt`
- Analizar el error
- Implementar fix

### 3. Linkear fix

```bash
dia fix --title "descripción del fix" --data-root /ruta/data --area it
```

### 4. Commit con referencia

```bash
dia pre-feat --data-root /ruta/data --area it
# Copiar y ejecutar comando sugerido (incluirá referencia a error)
```

### 5. Verificar trazabilidad

- Error capturado → `CaptureCreated`
- Fix linkeado → `FixLinked`
- Commit sugerido → `CommitSuggestionIssued` (con `error_ref`)

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

# Error 2
error2 2>&1 | dia cap --kind error --title "error 2" --data-root /ruta/data --area it

# Arreglar error 1
dia fix --title "fix error 1" --data-root /ruta/data --area it
# → Linkea al último (error 2)

# Arreglar error 2 (especificar capture_id)
dia fix --from cap_<id_error2> --title "fix error 2" --data-root /ruta/data --area it
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

## Próximos Pasos

- Integración con `close-day`: incluir métricas de errores capturados vs resueltos
- Análisis de patrones: detectar errores que reaparecen frecuentemente
- Sugerencias automáticas: proponer fixes basados en errores similares del historial

---

**Última actualización**: 2026-01-18  
**Versión del sistema**: v0.1+
