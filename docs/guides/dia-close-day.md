# dia close-day

Cierra la jornada (ritual humano). Solo registra el evento `DayClosed` y opcionalmente marca la bitácora.

## Uso

```bash
dia close-day
```

## Comportamiento

- **Registra evento `DayClosed`**: Se agrega a `data/index/events.ndjson`
- **Marca bitácora**: Si existe `data/bitacora/YYYY-MM-DD.md`, agrega marca de cierre en la sección automática
- **NO genera resúmenes**: Los resúmenes se generan con `dia summarize`
- **NO bloquea nuevas sesiones**: Se pueden iniciar sesiones después del cierre

## Nota importante

Este comando es un **ritual humano** que marca el fin de la jornada. No genera análisis ni resúmenes automáticos, y **no bloquea nuevas sesiones**.

Si inicias una sesión después de `dia close-day`:
- La sesión se permite normalmente
- Se genera evento `SessionStartedAfterDayClosed` en lugar de `SessionStarted`
- El ID de sesión sigue la secuencia normal (S02, S03, etc.)

Para generar resúmenes del día, ejecuta:
- `dia summarize --mode rolling` (durante el día)
- `dia summarize --mode nightly` (al final del día)

## Ejemplo

```bash
$ dia close-day
Jornada 2026-01-17 cerrada. Evento DayClosed registrado.
Nota: Para generar resúmenes, ejecuta 'dia summarize --mode rolling' o 'dia summarize --mode nightly'
```
