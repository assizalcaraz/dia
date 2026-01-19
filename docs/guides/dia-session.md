# dia session

Gestión de sesiones de trabajo. Una sesión representa un período de trabajo activo en un repositorio.

## Comandos

- `dia session start` - Inicia una sesión
- `dia session end` - Cierra una sesión activa
- `dia session pause` - Pausa una sesión activa
- `dia session resume` - Reanuda una sesión pausada

---

## dia session start

Inicia una nueva sesión de trabajo. Si no existe un `day_id` para el día actual, lo crea automáticamente.

### Uso

```bash
dia session start
dia session start --repo /path/to/repo
dia session start --intent "Implementar feature X" --dod "Feature funcionando y testeada"
```

### Argumentos

- `--repo` (opcional): Ruta del repositorio (default: directorio actual)
- `--intent` (opcional): Intención de la sesión (1 frase). Si no se proporciona, se solicita interactivamente.
- `--dod` (opcional): Definición de Hecho (DoD). Si no se proporciona, se solicita interactivamente.
- `--mode` (opcional): Modo de trabajo (default: `it`). Si no se proporciona, se solicita interactivamente.

### Comportamiento

1. **Valida repositorio**: Verifica que el directorio sea un repositorio Git válido
2. **Valida sesión activa**: Falla si ya hay una sesión activa (no pausada) en cualquier repositorio
3. **Crea day_id si no existe**: Si es el primer comando del día, crea automáticamente el `day_id` del día actual
4. **Genera ID de sesión**: Asigna un ID secuencial (S01, S02, S03, etc.) para el día
5. **Registra eventos**:
   - `SessionStarted` o `SessionStartedAfterDayClosed` (si el día ya estaba cerrado)
   - `RepoBaselineCaptured` (snapshot inicial del repositorio)
6. **Crea bitácora**: Agrega entrada en `data/bitacora/YYYY-MM-DD.md`
7. **Ejecuta repo-snapshot**: Captura automáticamente un snapshot de la estructura del repositorio

### Ejemplo

```bash
$ dia session start --intent "Implementar Feature Board" --dod "BoardView funcional con drag & drop"
Se usara 'dia' como nombre del proyecto.
Confirmar? (escriba 'no' para cancelar): 
Sesion S01 iniciada. Bitacora: data/bitacora/2026-01-18.md
```

### Notas

- Si el día ya está cerrado (`dia day close` ejecutado previamente), la sesión se permite pero se genera evento `SessionStartedAfterDayClosed`
- El comando falla si hay una sesión activa (no pausada). Usa `dia session end` o `dia session pause` primero.

---

## dia session end

Cierra la sesión activa actual. **NO genera resúmenes automáticamente**.

### Uso

```bash
dia session end
dia session end --repo /path/to/repo
```

### Argumentos

- `--repo` (opcional): Ruta del repositorio (default: directorio actual)

### Comportamiento

1. **Valida sesión activa**: Falla si no hay sesión activa para el repositorio
2. **Calcula diferencias**: Compara estado inicial vs final del repositorio
3. **Genera artefactos**:
   - `data/artifacts/YYYY-MM-DD/SXX_repo_diff_end.patch` - Diff completo
   - `data/bitacora/YYYY-MM-DD/CIERRE_SXX.md` - Archivo de cierre (legacy)
   - `data/bitacora/YYYY-MM-DD/LIMPIEZA_SXX.md` - Archivo de limpieza (legacy)
4. **Registra eventos**:
   - `RepoDiffComputed` - Diferencias calculadas
   - `CleanupTaskGenerated` - Tareas de limpieza sugeridas
   - `SessionEnded` - Cierre de sesión
5. **Actualiza bitácora**: Agrega información de cierre en `data/bitacora/YYYY-MM-DD.md`
6. **Ejecuta repo-audit**: Ejecuta automáticamente auditoría contra el snapshot inicial

### Ejemplo

```bash
$ dia session end
Sesion S01 cerrada. Bitacora jornada: data/bitacora/2026-01-18.md
```

### Notas

- **NO genera resúmenes**: Para generar resúmenes, usa `dia summary rolling` o `dia summary nightly`
- El comando funciona solo para la sesión del repositorio actual
- Los archivos `CIERRE_SXX.md` y `LIMPIEZA_SXX.md` se mantienen por compatibilidad pero la información principal está en la bitácora de jornada

---

## dia session pause

Pausa la sesión activa actual.

### Uso

```bash
dia session pause
dia session pause --repo /path/to/repo
dia session pause --reason "Pausa para reunión"
```

### Argumentos

- `--repo` (opcional): Ruta del repositorio (default: directorio actual)
- `--reason` (opcional): Razón de la pausa

### Comportamiento

1. **Valida sesión activa**: Falla si no hay sesión activa (no pausada) para el repositorio
2. **Registra evento**: `SessionPaused` en `data/index/events.ndjson`
3. **Actualiza bitácora**: Agrega marca de pausa en `data/bitacora/YYYY-MM-DD.md`

### Ejemplo

```bash
$ dia session pause --reason "Pausa para reunión"
Sesion S01 pausada.
```

### Notas

- Una sesión pausada no se considera "activa" para validaciones (ej: `dia day close` requiere que no haya sesiones activas)
- Para reanudar, usa `dia session resume`

---

## dia session resume

Reanuda una sesión pausada.

### Uso

```bash
dia session resume
dia session resume --repo /path/to/repo
```

### Argumentos

- `--repo` (opcional): Ruta del repositorio (default: directorio actual)

### Comportamiento

1. **Valida sesión pausada**: Falla si no hay sesión pausada para el repositorio
2. **Registra evento**: `SessionResumed` en `data/index/events.ndjson`
3. **Actualiza bitácora**: Agrega marca de reanudación en `data/bitacora/YYYY-MM-DD.md`

### Ejemplo

```bash
$ dia session resume
Sesion S01 reanudada.
```

### Notas

- Solo reanuda sesiones que están pausadas. Si la sesión ya está activa, el comando falla.

---

## Compatibilidad Legacy

Los siguientes comandos legacy siguen funcionando como aliases:

- `dia start` → `dia session start`
- `dia end` → `dia session end`
- `dia pause` → `dia session pause`
- `dia resume` → `dia session resume`

Se recomienda usar los nuevos comandos con namespace para mayor claridad.

---

## Referencias

- [dia day](dia-day.md) - Gestión de días/jornadas
- [dia summary](dia-summary.md) - Generación de resúmenes
- [Sesiones múltiples por día](sesiones-multiples.md) - Guía sobre múltiples sesiones

---

**Última actualización**: 2026-01-18
