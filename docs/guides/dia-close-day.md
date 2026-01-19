# dia close-day

**[LEGACY]** Alias de `dia day close`. Se recomienda usar `dia day close` para mayor claridad.

Cierra la jornada (ritual humano). Valida que no haya sesiones activas o pausadas, genera summary nightly automáticamente, y registra el evento `DayClosed`.

## Uso

```bash
dia close-day
dia close-day --skip-summary
```

**Recomendado**: Usa `dia day close` en su lugar.

## Comportamiento

1. **Valida día cerrado**: Falla si el día ya está cerrado
2. **Valida sesiones activas/pausadas**: Falla si hay sesiones activas o pausadas
   - Error: "Hay sesión activa o pausada: SXX"
   - Sugerencia: Ejecuta `dia session end` para cerrar todas las sesiones
3. **Genera summary nightly** (a menos que se use `--skip-summary`):
   - Ejecuta `dia summary nightly --force` automáticamente
   - Si falla, muestra advertencia pero continúa con el cierre
4. **Registra evento `DayClosed`**: Se agrega a `data/index/events.ndjson`
5. **Marca bitácora**: Si existe `data/bitacora/YYYY-MM-DD.md`, agrega marca de cierre en la sección automática

## Argumentos

- `--skip-summary` (opcional): Omite la generación automática de summary nightly

## Ejemplo

```bash
$ dia close-day
Generando summary nightly para 2026-01-18...
Resumen nightly generado para 2026-01-18
Assessment: ON_TRACK
Próximo paso: Continuar con siguiente tarea
Artefacto: artifacts/summaries/2026-01-18/nightly_20260118T230000.md
Jornada 2026-01-18 cerrada. Evento DayClosed registrado.
```

## Ejemplo con sesión activa (falla)

```bash
$ dia close-day
Error: Hay sesión activa o pausada: S01
Sugerencia: Ejecuta 'dia session end' para cerrar todas las sesiones antes de cerrar el día.
```

## Nota importante

Este comando es un **ritual humano** que marca el fin de la jornada. A diferencia de versiones anteriores:

- **Valida sesiones**: No permite cerrar el día si hay trabajo en curso (sesiones activas o pausadas)
- **Genera nightly automáticamente**: A menos que uses `--skip-summary`
- **NO bloquea nuevas sesiones**: Después de cerrar, se pueden iniciar nuevas sesiones (generan `SessionStartedAfterDayClosed`)

Si inicias una sesión después de `dia close-day`:
- La sesión se permite normalmente
- Se genera evento `SessionStartedAfterDayClosed` en lugar de `SessionStarted`
- El ID de sesión sigue la secuencia normal (S02, S03, etc.)

## Workflow Recomendado

1. Cerrar todas las sesiones activas:
   ```bash
   dia session end
   ```

2. Verificar estado:
   ```bash
   dia day status
   ```

3. Cerrar jornada:
   ```bash
   dia day close
   ```

## Referencias

- [dia day close](dia-day.md#dia-day-close) - Comando nuevo recomendado
- [dia session](dia-session.md) - Gestión de sesiones
- [dia summary](dia-summary.md) - Generación de resúmenes
