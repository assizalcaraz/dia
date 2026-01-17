# Sesiones múltiples por día

`/dia` permite **N sesiones por día** sin restricciones. Cada sesión se identifica con un ID secuencial (S01, S02, S03, etc.).

## Comportamiento

### Generación de IDs

Los IDs de sesión se generan automáticamente contando las sesiones iniciadas en el día:

- Primera sesión del día: `S01`
- Segunda sesión del día: `S02`
- Tercera sesión del día: `S03`
- Y así sucesivamente...

### Sesiones después de cierre

El comando `dia close-day` marca el día como cerrado, pero **no bloquea nuevas sesiones**.

Si inicias una sesión después de cerrar el día:

1. La sesión se permite normalmente
2. Se genera evento `SessionStartedAfterDayClosed` en lugar de `SessionStarted`
3. El ID de sesión sigue la secuencia normal (S02, S03, etc.)

**Ejemplo**:
```bash
# Día normal
$ dia start  # Genera S01, evento SessionStarted
$ dia end    # Cierra S01

$ dia start  # Genera S02, evento SessionStarted
$ dia end    # Cierra S02

$ dia close-day  # Marca día como cerrado

# Después del cierre
$ dia start  # Genera S03, evento SessionStartedAfterDayClosed
$ dia end    # Cierra S03
```

## Visualización en UI

La UI muestra:

- **Métrica "Sesiones hoy"**: Contador de todas las sesiones iniciadas en el día actual
- **Listado de sesiones de hoy**: En zona viva, muestra todas las sesiones del día con:
  - ID de sesión
  - Badge "Activa" si está en curso
  - Intent (si existe)
  - Hora de inicio
  - Hora de fin (si está cerrada)
  - Duración calculada

## API

El endpoint `/api/day/today` retorna:

```json
{
  "day_id": "2026-01-18",
  "sessions_count": 3,
  "sessions": [
    {
      "session_id": "S01",
      "start_ts": "2026-01-18T10:00:00-03:00",
      "end_ts": "2026-01-18T12:30:00-03:00",
      "elapsed_minutes": 150,
      "active": false,
      "intent": "...",
      "dod": "...",
      "repo": {...}
    },
    {
      "session_id": "S02",
      "start_ts": "2026-01-18T14:00:00-03:00",
      "end_ts": null,
      "elapsed_minutes": 45,
      "active": true,
      "intent": "...",
      "dod": "...",
      "repo": {...}
    }
  ],
  "closed": false,
  "closed_at": null
}
```

## Casos de uso

### Múltiples proyectos en un día

```bash
# Sesión 1: Proyecto A
$ cd /path/to/project-a
$ dia start --project project-a
# Trabajo...
$ dia end

# Sesión 2: Proyecto B
$ cd /path/to/project-b
$ dia start --project project-b
# Trabajo...
$ dia end
```

### Sesiones de emergencia después de cierre

```bash
# Día normal
$ dia start  # S01
$ dia end
$ dia close-day  # Marca día cerrado

# Emergencia
$ dia start  # S02 (SessionStartedAfterDayClosed)
# Fix urgente...
$ dia end
```

### Sesiones intercaladas

No hay problema en tener múltiples sesiones activas en diferentes repositorios. Cada sesión se identifica por su `session_id` único.

## Eventos relacionados

- `SessionStarted`: Sesión iniciada normalmente
- `SessionStartedAfterDayClosed`: Sesión iniciada después de `dia close-day`
- `SessionEnded`: Sesión cerrada
- `DayClosed`: Jornada cerrada (no bloquea nuevas sesiones)

Todos estos eventos se registran en `data/index/events.ndjson` y `data/index/sessions.ndjson`.
