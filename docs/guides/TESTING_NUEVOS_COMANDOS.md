# Guía de Pruebas: Nuevos Comandos CLI

Esta guía documenta cómo probar los nuevos comandos CLI con namespaces (`dia session`, `dia day`, `dia summary`) y verificar que funcionan correctamente.

---

## Prerequisitos

- CLI instalado y funcionando
- Repositorio Git válido para pruebas
- Acceso a `data/` directory configurado

---

## 1. Pruebas de Sesiones

### 1.1 dia session start

**Objetivo**: Verificar que inicia sesión correctamente y crea day_id si no existe.

**Pasos**:
```bash
# Limpiar estado previo (opcional)
rm -rf data/index/events.ndjson data/index/sessions.ndjson

# Iniciar sesión
dia session start \
  --intent "Prueba de sesión" \
  --dod "Verificar funcionamiento" \
  --data-root ./data

# Verificar eventos
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "SessionStarted"
cat data/index/events.ndjson | tail -1 | jq '.session.session_id'  # Debe ser "S01"
```

**Resultado esperado**:
- Sesión iniciada con ID S01
- Evento `SessionStarted` registrado
- Bitácora creada/actualizada
- No debe fallar

---

### 1.2 dia session pause

**Objetivo**: Verificar que pausa sesión activa correctamente.

**Pasos**:
```bash
# Asegurar que hay sesión activa (ejecutar 1.1 primero)
dia session pause --reason "Pausa de prueba" --data-root ./data

# Verificar evento
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "SessionPaused"
cat data/index/events.ndjson | tail -1 | jq '.payload.reason'  # Debe ser "Pausa de prueba"
```

**Resultado esperado**:
- Sesión pausada
- Evento `SessionPaused` registrado
- Bitácora actualizada

---

### 1.3 dia session resume

**Objetivo**: Verificar que reanuda sesión pausada correctamente.

**Pasos**:
```bash
# Asegurar que hay sesión pausada (ejecutar 1.1 y 1.2 primero)
dia session resume --data-root ./data

# Verificar evento
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "SessionResumed"
```

**Resultado esperado**:
- Sesión reanudada
- Evento `SessionResumed` registrado
- Bitácora actualizada

---

### 1.4 dia session end

**Objetivo**: Verificar que cierra sesión y NO genera nightly automáticamente.

**Pasos**:
```bash
# Asegurar que hay sesión activa (ejecutar 1.1 primero, o 1.1 + 1.2 + 1.3)
dia session end --data-root ./data

# Verificar evento
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "SessionEnded"

# Verificar que NO se generó nightly automáticamente
ls data/artifacts/summaries/$(date +%Y-%m-%d)/nightly_* 2>/dev/null || echo "OK: No se generó nightly (correcto)"
```

**Resultado esperado**:
- Sesión cerrada
- Evento `SessionEnded` registrado
- Bitácora actualizada
- **NO debe generar summary nightly automáticamente**

---

## 2. Pruebas de Días

### 2.1 dia day status

**Objetivo**: Verificar que muestra estado correcto del día.

**Pasos**:
```bash
# Con sesión activa
dia session start --intent "Test" --dod "Test" --data-root ./data
dia day status --data-root ./data

# Debe mostrar:
# - Día actual
# - Estado: Abierto
# - Sesiones activas: 1 (o más)
# - Lista de sesiones con información
```

**Resultado esperado**:
- Muestra día actual
- Lista sesiones activas correctamente
- Lista sesiones pausadas correctamente
- Indica si el día está cerrado

---

### 2.2 dia day close con sesión activa (debe fallar)

**Objetivo**: Verificar que falla si hay sesión activa.

**Pasos**:
```bash
# Asegurar que hay sesión activa
dia session start --intent "Test" --dod "Test" --data-root ./data

# Intentar cerrar día (debe fallar)
dia day close --data-root ./data
```

**Resultado esperado**:
- Error: "Hay sesión activa o pausada: SXX"
- Sugerencia: "Ejecuta 'dia session end' para cerrar todas las sesiones"
- **NO debe cerrar el día**
- **NO debe generar nightly**

---

### 2.3 dia day close sin sesiones (debe funcionar)

**Objetivo**: Verificar que cierra día y genera nightly automáticamente.

**Pasos**:
```bash
# Asegurar que NO hay sesiones activas
dia session end --data-root ./data  # Si hay sesión activa

# Cerrar día
dia day close --data-root ./data

# Verificar eventos
cat data/index/events.ndjson | grep -A 5 "DayClosed" | tail -1 | jq '.type'  # Debe ser "DayClosed"

# Verificar que se generó nightly
ls data/artifacts/summaries/$(date +%Y-%m-%d)/nightly_*  # Debe existir
```

**Resultado esperado**:
- Día cerrado
- Evento `DayClosed` registrado
- **Summary nightly generado automáticamente**
- Bitácora actualizada

---

### 2.4 dia day close --skip-summary

**Objetivo**: Verificar que puede omitir generación de nightly.

**Pasos**:
```bash
# Asegurar que NO hay sesiones activas
dia session end --data-root ./data  # Si hay sesión activa

# Cerrar día sin summary
dia day close --skip-summary --data-root ./data

# Verificar que NO se generó nightly
ls data/artifacts/summaries/$(date +%Y-%m-%d)/nightly_* 2>/dev/null && echo "ERROR: Se generó nightly" || echo "OK: No se generó nightly"
```

**Resultado esperado**:
- Día cerrado
- Evento `DayClosed` registrado
- **NO se generó summary nightly**

---

## 3. Pruebas de Resúmenes

### 3.1 dia summary rolling sin sesión activa (debe fallar)

**Objetivo**: Verificar que falla si no hay sesión activa.

**Pasos**:
```bash
# Asegurar que NO hay sesión activa
dia session end --data-root ./data  # Si hay sesión activa

# Intentar generar rolling (debe fallar)
dia summary rolling --data-root ./data
```

**Resultado esperado**:
- Error: "No hay sesión activa. Rolling summary requiere sesión activa."
- **NO debe generar resumen**

---

### 3.2 dia summary rolling con sesión activa (debe funcionar)

**Objetivo**: Verificar que genera rolling correctamente.

**Pasos**:
```bash
# Asegurar que hay sesión activa
dia session start --intent "Test" --dod "Test" --data-root ./data

# Generar rolling
dia summary rolling --data-root ./data

# Verificar artefacto
ls data/artifacts/summaries/$(date +%Y-%m-%d)/rolling_*  # Debe existir

# Verificar evento
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "RollingSummaryGenerated"
```

**Resultado esperado**:
- Resumen rolling generado
- Artefacto creado
- Evento `RollingSummaryGenerated` registrado

---

### 3.3 dia summary nightly sin día cerrado (debe advertir)

**Objetivo**: Verificar que advierte si el día no está cerrado.

**Pasos**:
```bash
# Asegurar que el día NO está cerrado
# (no ejecutar dia day close)

# Generar nightly (debe advertir)
dia summary nightly --data-root ./data
# Debe mostrar advertencia y solicitar confirmación
```

**Resultado esperado**:
- Advertencia: "Día YYYY-MM-DD no está cerrado"
- Sugerencia: "Ejecuta 'dia day close' primero, o usa --force para forzar"
- Solicita confirmación
- Si se confirma, genera nightly

---

### 3.4 dia summary nightly con día cerrado (debe funcionar)

**Objetivo**: Verificar que genera nightly correctamente cuando el día está cerrado.

**Pasos**:
```bash
# Cerrar día primero
dia session end --data-root ./data  # Si hay sesión activa
dia day close --data-root ./data

# Generar nightly
dia summary nightly --data-root ./data

# Verificar artefacto
ls data/artifacts/summaries/$(date +%Y-%m-%d)/nightly_*  # Debe existir

# Verificar evento
cat data/index/events.ndjson | tail -1 | jq '.type'  # Debe ser "DailySummaryGenerated"
```

**Resultado esperado**:
- Resumen nightly generado
- Artefacto creado
- Evento `DailySummaryGenerated` registrado
- No debe mostrar advertencias

---

### 3.5 dia summary nightly --force

**Objetivo**: Verificar que puede forzar generación aunque el día no esté cerrado.

**Pasos**:
```bash
# Asegurar que el día NO está cerrado
# (no ejecutar dia day close)

# Generar nightly con --force
dia summary nightly --force --data-root ./data

# Verificar artefacto
ls data/artifacts/summaries/$(date +%Y-%m-%d)/nightly_*  # Debe existir
```

**Resultado esperado**:
- Resumen nightly generado
- **NO debe mostrar advertencias**
- Artefacto creado

---

## 4. Pruebas de Compatibilidad Legacy

### 4.1 Comandos legacy funcionan

**Objetivo**: Verificar que comandos legacy siguen funcionando.

**Pasos**:
```bash
# dia start (alias de dia session start)
dia start --intent "Test" --dod "Test" --data-root ./data
dia session end --data-root ./data

# dia end (alias de dia session end)
dia session start --intent "Test" --dod "Test" --data-root ./data
dia end --data-root ./data

# dia close-day (alias de dia day close)
dia day close --data-root ./data

# dia summarize --mode rolling (alias de dia summary rolling)
dia session start --intent "Test" --dod "Test" --data-root ./data
dia summarize --mode rolling --data-root ./data
dia session end --data-root ./data

# dia summarize --mode nightly (alias de dia summary nightly)
dia day close --data-root ./data
dia summarize --mode nightly --data-root ./data
```

**Resultado esperado**:
- Todos los comandos legacy funcionan correctamente
- Comportamiento idéntico a los comandos nuevos

---

### 4.2 Help muestra ambos comandos

**Objetivo**: Verificar que help muestra comandos nuevos y legacy.

**Pasos**:
```bash
# Ver help principal
dia --help

# Ver help de session
dia session --help

# Ver help de day
dia day --help

# Ver help de summary
dia summary --help
```

**Resultado esperado**:
- Help principal muestra comandos nuevos (session, day, summary) y legacy (start, end, etc.)
- Help de namespaces muestra subcomandos correctamente
- Comandos legacy marcados como `[LEGACY]` donde corresponda

---

## 5. Pruebas de Flujo Completo

### 5.1 Flujo completo: Sesión → Cierre → Nightly

**Objetivo**: Verificar flujo completo de trabajo.

**Pasos**:
```bash
# 1. Iniciar sesión
dia session start --intent "Implementar feature X" --dod "Feature funcionando" --data-root ./data

# 2. Generar rolling durante trabajo
dia summary rolling --data-root ./data

# 3. Pausar sesión
dia session pause --reason "Reunión" --data-root ./data

# 4. Reanudar sesión
dia session resume --data-root ./data

# 5. Cerrar sesión
dia session end --data-root ./data

# 6. Verificar estado
dia day status --data-root ./data

# 7. Cerrar día (genera nightly automáticamente)
dia day close --data-root ./data

# 8. Verificar artefactos
ls -la data/artifacts/summaries/$(date +%Y-%m-%d)/
```

**Resultado esperado**:
- Todos los pasos funcionan correctamente
- Eventos registrados en orden correcto
- Artefactos generados correctamente
- Nightly generado automáticamente al cerrar día

---

## 6. Validación de Eventos

### 6.1 Verificar eventos en events.ndjson

**Objetivo**: Verificar que todos los eventos se registran correctamente.

**Pasos**:
```bash
# Ejecutar flujo completo (5.1)

# Verificar eventos
cat data/index/events.ndjson | jq -r '.type' | tail -10

# Debe incluir (en orden):
# - SessionStarted
# - RepoBaselineCaptured
# - RollingSummaryGenerated
# - SessionPaused
# - SessionResumed
# - SessionEnded
# - DayClosed
# - DailySummaryGenerated (si se generó nightly)
```

**Resultado esperado**:
- Todos los eventos registrados
- Orden correcto
- Estructura válida

---

## Notas de Pruebas

- **Limpieza**: Considera limpiar `data/index/events.ndjson` y `data/index/sessions.ndjson` antes de pruebas para resultados más claros
- **Aislamiento**: Cada prueba puede ejecutarse independientemente, pero algunas requieren estado previo
- **Verificación**: Usa `jq` para verificar estructura de eventos JSON
- **Artefactos**: Los artefactos se generan en `data/artifacts/summaries/YYYY-MM-DD/`

---

## Referencias

- [dia session](dia-session.md) - Documentación de comandos de sesión
- [dia day](dia-day.md) - Documentación de comandos de día
- [dia summary](dia-summary.md) - Documentación de comandos de resumen

---

**Última actualización**: 2026-01-18
