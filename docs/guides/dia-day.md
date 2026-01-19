# dia day

Gestión de días/jornadas. Un día representa una jornada de trabajo completa, que puede contener múltiples sesiones.

## Comandos

- `dia day status` - Muestra estado del día actual
- `dia day close` - Cierra la jornada (valida sesiones y genera nightly)

---

## dia day status

Muestra el estado del día actual: sesiones activas, pausadas, y si el día está cerrado.

### Uso

```bash
dia day status
```

### Comportamiento

1. **Lee eventos del día**: Filtra eventos de `data/index/events.ndjson` para el día actual
2. **Identifica sesiones**: Construye estado de todas las sesiones del día
3. **Clasifica sesiones**: Separa sesiones activas vs pausadas
4. **Verifica cierre**: Comprueba si el día está cerrado (`DayClosed`)

### Salida

Muestra:
- Día actual
- Estado (Abierto/Cerrado)
- Lista de sesiones activas con información básica
- Lista de sesiones pausadas con información básica

### Ejemplo

```bash
$ dia day status
Día: 2026-01-18
Estado: Abierto

Sesiones activas: 1
  - S01: /Users/joseassizalcarazbaxter/Developer/dia (inicio: 2026-01-18T10:00:00-03:00)
    Intent: Implementar Feature Board

Sesiones pausadas: 0

No hay sesiones activas o pausadas.
```

### Notas

- Útil para verificar estado antes de cerrar el día
- Muestra todas las sesiones del día, no solo las del repositorio actual

---

## dia day close

Cierra la jornada (ritual humano). Valida que no haya sesiones activas o pausadas, genera summary nightly automáticamente, y registra el evento `DayClosed`.

### Uso

```bash
dia day close
dia day close --skip-summary
```

### Argumentos

- `--skip-summary` (opcional): Omite la generación automática de summary nightly

### Comportamiento

1. **Valida día cerrado**: Falla si el día ya está cerrado
2. **Valida sesiones activas/pausadas**: Falla si hay sesiones activas o pausadas
   - Error: "Hay sesión activa o pausada: SXX"
   - Sugerencia: Ejecuta `dia session end` para cerrar todas las sesiones
3. **Genera summary nightly** (a menos que se use `--skip-summary`):
   - Ejecuta `dia summary nightly --force` automáticamente
   - Si falla, muestra advertencia pero continúa con el cierre
4. **Registra evento `DayClosed`**: Se agrega a `data/index/events.ndjson`
5. **Marca bitácora**: Si existe `data/bitacora/YYYY-MM-DD.md`, agrega marca de cierre

### Ejemplo

```bash
$ dia day close
Generando summary nightly para 2026-01-18...
Resumen nightly generado para 2026-01-18
Assessment: ON_TRACK
Próximo paso: Continuar con siguiente tarea
Artefacto: artifacts/summaries/2026-01-18/nightly_20260118T230000.md
Jornada 2026-01-18 cerrada. Evento DayClosed registrado.
```

### Ejemplo con sesión activa (falla)

```bash
$ dia day close
Error: Hay sesión activa o pausada: S01
Sugerencia: Ejecuta 'dia session end' para cerrar todas las sesiones antes de cerrar el día.
```

### Notas

- **Ritual humano**: Este comando marca el fin de la jornada de forma consciente
- **Valida sesiones**: No permite cerrar el día si hay trabajo en curso
- **Genera nightly automáticamente**: A menos que uses `--skip-summary`
- **NO bloquea nuevas sesiones**: Después de cerrar, se pueden iniciar nuevas sesiones (generan `SessionStartedAfterDayClosed`)

### Workflow Recomendado

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

---

## Compatibilidad Legacy

El siguiente comando legacy sigue funcionando como alias:

- `dia close-day` → `dia day close`

Se recomienda usar `dia day close` para mayor claridad.

---

## Referencias

- [dia session](dia-session.md) - Gestión de sesiones
- [dia summary](dia-summary.md) - Generación de resúmenes
- [Sesiones múltiples por día](sesiones-multiples.md) - Guía sobre múltiples sesiones

---

**Última actualización**: 2026-01-18
