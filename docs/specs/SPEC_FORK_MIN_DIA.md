# /dia — SPEC fork mínimo (autonomía total en staging)

Este documento fija el alcance del fork mínimo de `/dia` y define **autonomía total en staging con impacto acotado**. No es implementación, es contrato operativo.

---

## Decisión central
**Autonomía total, impacto acotado.**

El agente puede actuar sin confirmación humana **solo en staging**, con gates obligatorios, evidencia completa y límites estrictos.

---

## Alcance y no-objetivos

### Incluye
- CLI mínima: `start`, `note`, `end`.
- NDJSON append-only para eventos.
- Bitácora inmutable por sesión.
- Artefactos vinculados (diffs, logs, stats, URLs).
- Autonomía total en staging con gates automáticos y auditoría.

### No incluye
- Supervisor/daemon permanente.
- Auto-fix sin evidencia o fuera de staging.
- Modificar producción sin confirmación humana.
- Reescritura de historial o borrado de evidencia.

---

## Principios de autonomía (staging)

Toda acción autónoma en staging debe ser reversible mediante rollback automático o procedimiento documentado.

### Permitido sin confirmación
En **staging**, el agente puede:
- crear branches
- modificar código
- ejecutar tests y linters
- generar commits con convención definida
- fragmentar commits si superan umbral de tamaño
- desplegar a staging
- verificar healthchecks post-deploy
- generar artefactos (diffs, logs, stats)
- notificar resultados (email/webhook) con link navegable

### Límites estrictos (no negociables)
El agente **no puede** sin confirmación explícita:
- desplegar a producción
- modificar credenciales de prod
- tocar infraestructura compartida
- ejecutar comandos fuera del scope definido
- borrar evidencia o reescribir historial

---

## Gates automáticos obligatorios (previos a deploy)

Antes de cualquier deploy autónomo a staging deben pasar:
- tests unitarios
- lint/format
- migraciones controladas
- healthcheck post-deploy

Si un gate falla:
- no se despliega
- se notifica con propuesta de acción
- se registra el evento

---

## Comunicación como interfaz humana

El rol de comunicación se denomina **Agente Mensajero**. Su función es comunicar estado y resultados, no ejecutar cambios.

Al finalizar el ciclo autónomo, el agente debe enviar un resumen con:
- link directo a staging (mobile-friendly)
- checklist breve de validación
- resumen técnico de cambios
- instrucciones claras de respuesta:
  - `OK` -> promover (si está habilitado)
  - `NO: <motivo>` -> rollback + tarea

Las respuestas humanas se registran como eventos y alimentan la próxima sesión.

---

## Evidencia y auditoría (obligatorio)

Toda acción autónoma debe generar:
- eventos NDJSON (append-only)
- artefactos enlazados (diffs, logs, URLs)
- referencia a sesión y objetivo

Sin evidencia, la acción se considera inválida.

---

## Contrato con proyectos externos

`/dia` sigue siendo **repo de registro** y **no se convierte en core**.  
El agente puede operar **solo** en un repo objetivo cuando se cumple:
- entorno staging confirmado
- scope de comandos definido
- gates activos y auditables
- evidencia completa generada

Fuera de ese contexto, `/dia` **no edita proyectos**.

El scope de comandos permitidos debe estar explicitado (p. ej. allowlist de comandos git/deploy/test). Fuera de ese scope se requiere confirmación humana.

---

## Lectura política (criterio de fondo)

Este SPEC no busca “hacer segura” la IA prohibiéndola ni “hacerla libre” soltándole la correa.  
Le asigna responsabilidad en un territorio donde equivocarse es barato: **staging primero**.

---

## Eventos recomendados (NDJSON)

Eventos base ya definidos en [`docs/specs/NDJSON.md`](NDJSON.md):
- `SessionStarted`, `SessionEnded`
- `RepoBaselineCaptured`, `RepoDiffComputed`
- `CommitCreated`, `CommitOverdue`, `LargeCommitDetected`
- `CleanupTaskGenerated`

Eventos adicionales sugeridos para autonomía en staging:
- `GateFailed`
- `AutoFixApplied`
- `AutoCommitCreated`
- `StagingDeployStarted`
- `StagingDeploySucceeded`
- `StagingDeployFailed`
- `HealthcheckFailed`
- `SummaryNotified`
- `HumanResponseCaptured`
- `RollbackExecuted`

---

## Ejemplos NDJSON (staging)

Cada bloque es **una línea** NDJSON.

### GateFailed
```json
{"event_id":"evt_01J4GATEFAIL00","ts":"2026-01-18T12:04:21-03:00","type":"GateFailed","session":{"day_id":"2026-01-18","session_id":"S03","intent":"Autonomía staging con gates","mode":"it"},"actor":{"user_id":"dia","user_type":"agent","role":"auxiliar","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":{"path":"/path/to/surfix","vcs":"git","branch":"staging","start_sha":"a1b2c3d4","end_sha":null,"dirty":true},"payload":{"gate":"tests","command":"pytest -q","exit_code":1,"summary":"2 tests failed"},"links":[{"kind":"artifact","ref":"artifacts/S03_tests.log"}]}
```

### StagingDeploySucceeded
```json
{"event_id":"evt_01J4STGOK0001","ts":"2026-01-18T12:28:10-03:00","type":"StagingDeploySucceeded","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"operador","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":{"path":"/path/to/surfix","vcs":"git","branch":"staging","start_sha":"a1b2c3d4","end_sha":"f0e1d2c3","dirty":false},"payload":{"deploy_target":"staging","commit":"f0e1d2c3","duration_sec":184,"strategy":"blue-green"},"links":[{"kind":"artifact","ref":"artifacts/S03_deploy.log"},{"kind":"url","ref":"https://staging.example.com"}]}
```

### SummaryNotified
```json
{"event_id":"evt_01J4SUMMARY01","ts":"2026-01-18T12:35:02-03:00","type":"SummaryNotified","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"auxiliar","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":null,"payload":{"channel":"webhook","to":"https://hooks.example.com/summary","summary":"Deploy OK en staging, healthcheck OK, listo para validar.","checklist":["/login","/dashboard","/api/health"],"response_hint":"OK o NO: <motivo>"},"links":[{"kind":"url","ref":"https://staging.example.com"}]}
```

### HumanResponseCaptured
```json
{"event_id":"evt_01J4HUMANOK01","ts":"2026-01-18T12:44:55-03:00","type":"HumanResponseCaptured","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"u_assiz","user_type":"human","role":"director","client":"email"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":null,"payload":{"response":"OK","notes":"Validado flujo principal, promover."},"links":[{"kind":"url","ref":"https://staging.example.com"}]}
```

### RollbackExecuted
```json
{"event_id":"evt_01J4ROLLBK01","ts":"2026-01-18T12:50:31-03:00","type":"RollbackExecuted","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"operador","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":{"path":"/path/to/surfix","vcs":"git","branch":"staging","start_sha":"a1b2c3d4","end_sha":"d4c3b2a1","dirty":false},"payload":{"reason":"HumanResponse","from_commit":"f0e1d2c3","to_commit":"d4c3b2a1","method":"auto_rollback"},"links":[{"kind":"artifact","ref":"artifacts/S03_rollback.log"}]}
```

### AutoFixApplied
```json
{"event_id":"evt_01J4AUTOFIX01","ts":"2026-01-18T12:12:05-03:00","type":"AutoFixApplied","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"operador","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":{"path":"/path/to/surfix","vcs":"git","branch":"staging","start_sha":"a1b2c3d4","end_sha":null,"dirty":true},"payload":{"fix":"format","command":"ruff format .","files_changed":6},"links":[{"kind":"artifact","ref":"artifacts/S03_format.log"}]}
```

### AutoCommitCreated
```json
{"event_id":"evt_01J4AUTOCOM01","ts":"2026-01-18T12:14:33-03:00","type":"AutoCommitCreated","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"operador","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":{"path":"/path/to/surfix","vcs":"git","branch":"staging","start_sha":"a1b2c3d4","end_sha":"b2c3d4e5","dirty":false},"payload":{"sha":"b2c3d4e5","summary":"chore: format code [#sesion S03]","files_changed":6,"additions":120,"deletions":118},"links":[{"kind":"artifact","ref":"artifacts/S03_commit_stats.json"}]}
```

### HealthcheckFailed
```json
{"event_id":"evt_01J4HEALTHKO1","ts":"2026-01-18T12:30:02-03:00","type":"HealthcheckFailed","session":{"day_id":"2026-01-18","session_id":"S03"},"actor":{"user_id":"dia","user_type":"agent","role":"auxiliar","client":"cli"},"project":{"tag":"surfix","area":"it","context":"staging"},"repo":null,"payload":{"url":"https://staging.example.com/health","status_code":500,"timeout_ms":2000,"retry_count":3},"links":[{"kind":"artifact","ref":"artifacts/S03_healthcheck.log"},{"kind":"url","ref":"https://staging.example.com"}]}
```

---

## Artefactos mínimos

Cada ciclo autónomo en staging debe adjuntar:
- diff de cambios
- logs de tests/lint/migraciones
- log de deploy
- resultado de healthcheck
- URL de staging

---

## Promoción a producción

- Solo mediante respuesta humana `OK`.
- Autopromote queda fuera de alcance (futuro, con reglas duras y monitoreo).

---

## Mapa de rescate (cantera)

### Desde `pre_cursor`
- Auditoría de repo (baseline, diff, archivos sospechosos).
- Reglas de archivos sospechosos.
- Pipeline de docs **solo como sugerencias**.
- Excluir daemon y AutoExecutor.

### Desde `task_manager`
- Uso de Markdown para contenido.
- Tags semánticos si aplica a notas/tareas en `/dia`.

---

## Roadmap sugerido

1. Autonomía total en staging (deploy + notificación).
2. Promoción a producción solo por respuesta humana `OK`.
3. Autopromote a producción con reglas duras y monitoreo (futuro).
