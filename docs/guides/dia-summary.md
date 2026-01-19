# dia summary

Generación de resúmenes regenerables. Los resúmenes son vistas derivadas de los eventos del día que proporcionan análisis y veredictos sobre el progreso.

## Comandos

- `dia summary rolling` - Resumen liviano incremental para sesión activa
- `dia summary nightly` - Informe largo consolidado del día

---

## dia summary rolling

Genera un resumen rolling (estado liviano incremental) para la sesión activa actual.

### Uso

```bash
dia summary rolling
dia summary rolling --day-id 2026-01-17
```

### Argumentos

- `--day-id` (opcional): Día específico en formato `YYYY-MM-DD` (default: día actual)

### Comportamiento

1. **Valida sesión activa**: Falla si no hay sesión activa
2. **Lee eventos del día**: Filtra eventos de `data/index/events.ndjson` para el día especificado
3. **Extrae objetivo**: Lee objetivo de la bitácora `data/bitacora/YYYY-MM-DD.md` (sección manual)
4. **Analiza eventos**: Aplica heurísticas para determinar veredicto:
   - `BLOCKED`: Hay errores sin fix (`CaptureCreated` sin `FixLinked`)
   - `OFF_TRACK`: Hay `CommitOverdue` o actividad sin commits
   - `ON_TRACK`: Sesiones cerradas y progreso normal
5. **Calcula delta**: Compara con último resumen rolling (si existe) para mostrar cambios
6. **Genera artefactos**:
   - `data/artifacts/summaries/YYYY-MM-DD/rolling_<timestamp>.md`
   - `data/artifacts/summaries/YYYY-MM-DD/rolling_<timestamp>.json`
7. **Registra evento**: Agrega `RollingSummaryGenerated` a:
   - `data/index/events.ndjson`
   - `data/index/summaries.ndjson` (índice append-only)

### Ejemplo

```bash
$ dia summary rolling
Resumen rolling generado para 2026-01-18
Assessment: ON_TRACK
Próximo paso: Continuar trabajando
Artefacto: artifacts/summaries/2026-01-18/rolling_20260118T101500.md
```

### Ejemplo sin sesión activa (falla)

```bash
$ dia summary rolling
Error: No hay sesión activa. Rolling summary requiere sesión activa.
```

### Notas

- **Requiere sesión activa**: Solo se puede generar durante una sesión activa
- **Regenerable**: Puede ejecutarse múltiples veces durante el día
- **Incremental**: Cada ejecución genera un nuevo artefacto versionado (timestamp único)
- **Liviano**: Diseñado para ejecutarse frecuentemente (ej: cada 15 minutos con cron)

### Automatización con cron

```cron
# Rolling cada 15 minutos
*/15 * * * * dia summary rolling --data-root /path/to/data >> /path/to/logs/cron.log 2>&1
```

---

## dia summary nightly

Genera un resumen nightly (informe largo consolidado) del día. Idealmente requiere que el día esté cerrado.

### Uso

```bash
dia summary nightly
dia summary nightly --day-id 2026-01-17
dia summary nightly --force
```

### Argumentos

- `--day-id` (opcional): Día específico en formato `YYYY-MM-DD` (default: día actual)
- `--force` (opcional): Fuerza generación aunque el día no esté cerrado

### Comportamiento

1. **Lee eventos del día**: Filtra eventos de `data/index/events.ndjson` para el día especificado
2. **Valida día cerrado** (a menos que se use `--force`):
   - Si el día no está cerrado, muestra advertencia y solicita confirmación
   - Con `--force`, omite la validación
3. **Extrae objetivo**: Lee objetivo de la bitácora `data/bitacora/YYYY-MM-DD.md` (sección manual)
4. **Analiza eventos**: Aplica heurísticas para determinar veredicto (mismo que rolling)
5. **Genera artefactos**:
   - `data/artifacts/summaries/YYYY-MM-DD/nightly_<timestamp>.md`
   - `data/artifacts/summaries/YYYY-MM-DD/nightly_<timestamp>.json`
6. **Registra evento**: Agrega `DailySummaryGenerated` a:
   - `data/index/events.ndjson`
   - `data/index/summaries.ndjson` (índice append-only)

### Ejemplo

```bash
$ dia summary nightly
Resumen nightly generado para 2026-01-18
Assessment: ON_TRACK
Próximo paso: Continuar con siguiente tarea o cerrar sesión actual
Artefacto: artifacts/summaries/2026-01-18/nightly_20260118T230000.md
```

### Ejemplo con día no cerrado (advertencia)

```bash
$ dia summary nightly
Advertencia: Día 2026-01-18 no está cerrado.
Sugerencia: Ejecuta 'dia day close' primero, o usa --force para forzar.
¿Continuar de todas formas? (escriba 'si' para confirmar): si
Resumen nightly generado para 2026-01-18
...
```

### Ejemplo con --force

```bash
$ dia summary nightly --force
Resumen nightly generado para 2026-01-18
...
```

### Notas

- **Idealmente requiere día cerrado**: Se recomienda ejecutar después de `dia day close`
- **Puede forzarse**: Usa `--force` si necesitas generar antes del cierre
- **Consolidado**: Diseñado para ejecutarse una vez al final del día
- **Largo**: Incluye análisis completo de todas las sesiones del día

### Automatización con cron

```cron
# Nightly una vez al día, 23:00
0 23 * * * dia summary nightly --data-root /path/to/data >> /path/to/logs/cron.log 2>&1
```

**Nota**: Si usas cron, considera ejecutar `dia day close` antes del nightly, o usar `--force` si el cierre es manual.

---

## Diferencias: Rolling vs Nightly

| Característica | Rolling | Nightly |
|----------------|---------|---------|
| **Frecuencia** | Múltiples veces al día | Una vez al final del día |
| **Requisito** | Sesión activa | Día cerrado (recomendado) |
| **Propósito** | Estado incremental durante trabajo | Análisis consolidado final |
| **Tamaño** | Liviano | Largo |
| **Uso** | Durante desarrollo | Al finalizar jornada |

---

## Estructura del Resumen

Ambos tipos de resumen incluyen:

- **Assessment**: Estado actual (`ON_TRACK`, `OFF_TRACK`, `BLOCKED`)
- **Next step**: Próxima acción concreta sugerida
- **Blocker**: Bloqueador actual (si existe)
- **Risks**: Lista de riesgos detectados
- **Delta**: Cambios desde último resumen rolling (solo rolling)
- **Objective**: Objetivo del día (extraído de bitácora)

---

## Heurísticas de Veredicto

### BLOCKED
- Hay `CaptureCreated` sin `FixLinked` asociado
- Blocker muestra cantidad de errores sin resolver

### OFF_TRACK
- Hay evento `CommitOverdue`
- O hay actividad reciente pero 0 commits sugeridos

### ON_TRACK
- Sesiones cerradas y progreso normal
- Sin bloqueadores detectados

---

## Regeneración

Los resúmenes son **vistas derivadas regenerables**:

- Cada ejecución genera un nuevo artefacto versionado (timestamp único)
- Cada ejecución agrega una entrada al índice (append-only)
- Los resúmenes anteriores **nunca se reescriben**

Puedes ejecutar `dia summary rolling` múltiples veces durante el día sin perder información histórica.

---

## Compatibilidad Legacy

El siguiente comando legacy sigue funcionando como alias:

- `dia summarize --mode rolling` → `dia summary rolling`
- `dia summarize --mode nightly` → `dia summary nightly`

Se recomienda usar los nuevos comandos con namespace para mayor claridad.

---

## Referencias

- [dia session](dia-session.md) - Gestión de sesiones
- [dia day](dia-day.md) - Gestión de días/jornadas
- [dia summarize](dia-summarize.md) - Documentación legacy completa

---

**Última actualización**: 2026-01-18
