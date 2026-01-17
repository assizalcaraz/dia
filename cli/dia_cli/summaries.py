from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import config
from .utils import day_id, now_iso, read_json_lines, read_text


def extract_objective(jornada_path: Path) -> str:
    """Extrae el objetivo principal de la bitácora de jornada."""
    if not jornada_path.exists():
        return "No especificado"
    
    content = read_text(jornada_path)
    if "## 1. Intención del día (manual)" not in content:
        return "No especificado"
    
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if "Objetivo principal:" in line and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if next_line and not next_line.startswith("-"):
                return next_line.replace("-", "").strip()
    
    return "No especificado"


def analyze_events(events: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Analiza eventos para generar veredicto usando heurísticas.
    Retorna dict con: assessment, next_step, blocker, risks
    """
    assessment = "ON_TRACK"
    blocker = None
    risks = []
    next_step = "Continuar trabajando"
    
    # Recopilar información de eventos
    captures_without_fix = []
    commit_suggestions = []
    session_events = []
    commit_overdue = False
    
    for event in events:
        event_type = event.get("type")
        
        if event_type == "CaptureCreated":
            error_hash = event.get("payload", {}).get("error_hash")
            if error_hash:
                captures_without_fix.append(event)
        
        elif event_type == "FixLinked":
            error_hash = event.get("payload", {}).get("error_hash")
            # Remover de captures_without_fix si existe
            captures_without_fix = [
                c for c in captures_without_fix
                if c.get("payload", {}).get("error_hash") != error_hash
            ]
        
        elif event_type == "CommitSuggestionIssued":
            commit_suggestions.append(event)
        
        elif event_type == "SessionStarted":
            session_events.append(event)
        
        elif event_type == "SessionEnded":
            session_events.append(event)
        
        elif event_type == "CommitOverdue":
            commit_overdue = True
    
    # Heurística 1: BLOCKED si hay errores sin fix
    if captures_without_fix:
        assessment = "BLOCKED"
        blocker = f"{len(captures_without_fix)} error(es) sin fix"
        next_step = f"Resolver {len(captures_without_fix)} error(es) abierto(s) antes de continuar"
        risks.append("Errores sin resolver bloquean progreso")
    
    # Heurística 2: OFF_TRACK si hay CommitOverdue o 0 commits con actividad
    elif commit_overdue:
        assessment = "OFF_TRACK"
        next_step = "Ejecutar 'dia pre-feat' para hacer commit de cambios pendientes"
        risks.append("Cambios sin commit pueden perderse")
    
    elif len(commit_suggestions) == 0 and len(session_events) > 0:
        # Hay sesiones pero no hay commits sugeridos
        # Verificar si hay actividad reciente
        recent_activity = any(
            e.get("type") in ("CaptureCreated", "RepoDiffComputed")
            for e in events[-10:]  # Últimos 10 eventos
        )
        if recent_activity:
            assessment = "OFF_TRACK"
            next_step = "Revisar cambios y ejecutar 'dia pre-feat' si hay trabajo pendiente"
            risks.append("Actividad sin commits registrados")
    
    # Heurística 3: ON_TRACK si hay sesiones cerradas y progreso
    if assessment == "ON_TRACK":
        closed_sessions = sum(
            1 for e in events if e.get("type") == "SessionEnded"
        )
        if closed_sessions > 0:
            next_step = "Continuar con siguiente tarea o cerrar sesión actual"
        else:
            next_step = "Trabajar en tareas del día"
    
    return {
        "assessment": assessment,
        "next_step": next_step,
        "blocker": blocker,
        "risks": risks,
    }


def compute_delta(
    current_events: list[dict[str, Any]],
    previous_summary: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """
    Calcula delta entre eventos actuales y último resumen rolling.
    Retorna dict con: new_events, new_commits, new_errors, assessment_changed
    """
    if not previous_summary:
        # Primer resumen del día
        return {
            "new_events": [e.get("event_id") for e in current_events],
            "new_commits": sum(
                1 for e in current_events
                if e.get("type") == "CommitSuggestionIssued"
            ),
            "new_errors": sum(
                1 for e in current_events
                if e.get("type") == "CaptureCreated"
            ),
            "assessment_changed": False,
        }
    
    # Obtener timestamp del último resumen
    last_ts = previous_summary.get("ts", "")
    
    # Filtrar eventos nuevos (después del último resumen)
    new_events = [
        e for e in current_events
        if e.get("ts", "") > last_ts
    ]
    
    previous_assessment = previous_summary.get("payload", {}).get("assessment")
    current_analysis = analyze_events(current_events)
    current_assessment = current_analysis["assessment"]
    
    return {
        "new_events": [e.get("event_id") for e in new_events],
        "new_commits": sum(
            1 for e in new_events
            if e.get("type") == "CommitSuggestionIssued"
        ),
        "new_errors": sum(
            1 for e in new_events
            if e.get("type") == "CaptureCreated"
        ),
        "assessment_changed": previous_assessment != current_assessment,
    }


def find_last_rolling_summary(
    summaries_path: Path, day_id_val: str
) -> Optional[dict[str, Any]]:
    """Encuentra el último resumen rolling del día."""
    if not summaries_path.exists():
        return None
    
    summaries = list(read_json_lines(summaries_path))
    
    # Filtrar resúmenes del día y modo rolling
    day_rolling = [
        s for s in summaries
        if s.get("session", {}).get("day_id") == day_id_val
        and s.get("payload", {}).get("mode") == "rolling"
    ]
    
    if not day_rolling:
        return None
    
    # Ordenar por timestamp y retornar el más reciente
    day_rolling.sort(key=lambda s: s.get("ts", ""), reverse=True)
    return day_rolling[0]


def build_summary_payload(
    day_id_val: str,
    mode: str,
    window_start: str,
    window_end: str,
    summary_version: str,
    events: list[dict[str, Any]],
    objective: str,
    previous_summary: Optional[dict[str, Any]],
    artifact_ref: str,
) -> dict[str, Any]:
    """Construye el payload completo del evento de resumen."""
    analysis = analyze_events(events)
    delta = compute_delta(events, previous_summary)
    
    return {
        "day_id": day_id_val,
        "mode": mode,
        "window_start": window_start,
        "window_end": window_end,
        "summary_version": summary_version,
        "assessment": analysis["assessment"],
        "next_step": analysis["next_step"],
        "blocker": analysis["blocker"],
        "risks": analysis["risks"],
        "delta": delta,
        "objective": objective,
        "links": [{"kind": "artifact", "ref": artifact_ref}],
    }


def generate_summary(
    root: Path,
    day_id_val: str,
    mode: str,
    events: list[dict[str, Any]],
    objective: str,
    summaries_path: Path,
) -> dict[str, Any]:
    """
    Genera un resumen completo (artefactos + evento).
    Retorna el evento generado.
    """
    from .templates import rolling_summary_template, nightly_summary_template
    
    # Calcular ventana temporal
    if events:
        window_start = min(e.get("ts", "") for e in events)
        window_end = max(e.get("ts", "") for e in events)
    else:
        window_start = now_iso()
        window_end = now_iso()
    
    # Generar version basada en timestamp
    ts_for_version = datetime.fromisoformat(window_end.replace("Z", "+00:00"))
    version_suffix = ts_for_version.strftime("%Y%m%dT%H%M%S")
    summary_version = f"{mode}_{version_suffix}"
    
    # Buscar último resumen rolling para delta
    previous_summary = None
    if mode == "rolling":
        previous_summary = find_last_rolling_summary(summaries_path, day_id_val)
    
    # Crear directorio de artefactos
    artifacts_dir = config.summaries_artifacts_dir(root, day_id_val)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    
    # Generar artefactos
    artifact_md_path = artifacts_dir / f"{summary_version}.md"
    artifact_json_path = artifacts_dir / f"{summary_version}.json"
    
    # Construir payload
    artifact_ref = f"artifacts/summaries/{day_id_val}/{summary_version}.md"
    payload = build_summary_payload(
        day_id_val=day_id_val,
        mode=mode,
        window_start=window_start,
        window_end=window_end,
        summary_version=summary_version,
        events=events,
        objective=objective,
        previous_summary=previous_summary,
        artifact_ref=artifact_ref,
    )
    
    # Generar markdown según modo
    if mode == "rolling":
        summary_md = rolling_summary_template(
            day_id=day_id_val,
            timestamp=window_end,
            assessment=payload["assessment"],
            objective=objective,
            next_step=payload["next_step"],
            blocker=payload["blocker"],
            risks=payload["risks"],
            delta=payload["delta"],
        )
    else:  # nightly
        summary_md = nightly_summary_template(
            day_id=day_id_val,
            timestamp=window_end,
            assessment=payload["assessment"],
            objective=objective,
            next_step=payload["next_step"],
            blocker=payload["blocker"],
            risks=payload["risks"],
            delta=payload["delta"],
        )
    
    # Escribir artefactos
    from .utils import write_text
    write_text(artifact_md_path, summary_md)
    write_text(artifact_json_path, json.dumps(payload, indent=2, ensure_ascii=False))
    
    # Retornar payload y metadata para que el caller construya el evento
    return {
        "event_type": "RollingSummaryGenerated" if mode == "rolling" else "DailySummaryGenerated",
        "session": {"day_id": day_id_val, "session_id": None},
        "actor": {
            "user_id": "u_local",
            "user_type": "system" if mode == "nightly" else "human",
            "role": "cronista",
            "client": "cli",
        },
        "project": {"tag": None, "area": "it", "context": ""},
        "repo": None,
        "payload": payload,
        "links": payload["links"],
    }
