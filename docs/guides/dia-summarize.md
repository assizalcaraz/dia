# dia summarize

Genera resúmenes regenerables (rolling o nightly) como vistas derivadas de los eventos del día.

## Uso

```bash
dia summarize --mode rolling
dia summarize --mode nightly
dia summarize --mode rolling --day-id 2026-01-17
```

## Argumentos

- `--mode` (requerido): `rolling` | `nightly`
  - `rolling`: Resumen regenerable durante el día (puede ejecutarse múltiples veces)
  - `nightly`: Resumen generado al final del día (típicamente por cron)
- `--scope` (opcional, default: `day`): Alcance del resumen
  - `day`: Resumen del día completo (único soportado en v0)
- `--day-id` (opcional): Día específico en formato `YYYY-MM-DD` (default: día actual)

## Comportamiento

1. **Lee eventos del día**: Filtra eventos de `data/index/events.ndjson` para el día especificado
2. **Extrae objetivo**: Lee objetivo de la bitácora `data/bitacora/YYYY-MM-DD.md` (sección manual)
3. **Analiza eventos**: Aplica heurísticas para determinar veredicto:
   - `BLOCKED`: Hay errores sin fix (`CaptureCreated` sin `FixLinked`)
   - `OFF_TRACK`: Hay `CommitOverdue` o actividad sin commits
   - `ON_TRACK`: Sesiones cerradas y progreso normal
4. **Calcula delta**: Compara con último resumen rolling (si existe) para mostrar cambios
5. **Genera artefactos**:
   - `data/artifacts/summaries/YYYY-MM-DD/rolling_<timestamp>.md`
   - `data/artifacts/summaries/YYYY-MM-DD/rolling_<timestamp>.json`
6. **Registra evento**: Agrega `RollingSummaryGenerated` o `DailySummaryGenerated` a:
   - `data/index/events.ndjson`
   - `data/index/summaries.ndjson` (índice append-only)

## Ejemplos

### Resumen rolling (durante el día)

```bash
$ dia summarize --mode rolling
Resumen rolling generado para 2026-01-17
Assessment: ON_TRACK
Próximo paso: Continuar trabajando
Artefacto: artifacts/summaries/2026-01-17/rolling_20260117T101500.md
```

### Resumen nightly (final del día)

```bash
$ dia summarize --mode nightly
Resumen nightly generado para 2026-01-17
Assessment: ON_TRACK
Próximo paso: Continuar con siguiente tarea o cerrar sesión actual
Artefacto: artifacts/summaries/2026-01-17/nightly_20260117T230000.md
```

## Automatización con cron

### Rolling (cada 15 minutos)

```cron
*/15 * * * * dia summarize --scope day --mode rolling --data-root /path/to/data >> /path/to/logs/cron.log 2>&1
```

### Nightly (una vez al día, 23:00)

```cron
0 23 * * * dia summarize --scope day --mode nightly --data-root /path/to/data >> /path/to/logs/cron.log 2>&1
```

## Regeneración

Los resúmenes son **vistas derivadas regenerables**. Puedes ejecutar `dia summarize --mode rolling` múltiples veces durante el día:

- Cada ejecución genera un nuevo artefacto versionado (timestamp único)
- Cada ejecución agrega una entrada al índice (append-only)
- Los resúmenes anteriores **nunca se reescriben**

## Estructura del resumen

El resumen incluye:

- **Assessment**: Estado actual (`ON_TRACK`, `OFF_TRACK`, `BLOCKED`)
- **Next step**: Próxima acción concreta sugerida
- **Blocker**: Bloqueador actual (si existe)
- **Risks**: Lista de riesgos detectados
- **Delta**: Cambios desde último resumen rolling
- **Objective**: Objetivo del día (extraído de bitácora)

## Heurísticas de veredicto

### BLOCKED
- Hay `CaptureCreated` sin `FixLinked` asociado
- Blocker muestra cantidad de errores sin resolver

### OFF_TRACK
- Hay evento `CommitOverdue`
- O hay actividad reciente pero 0 commits sugeridos

### ON_TRACK
- Sesiones cerradas y progreso normal
- Sin bloqueadores detectados
