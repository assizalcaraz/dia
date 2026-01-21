from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .utils import read_json_lines


def next_session_id(day_id: str, sessions_path: Path) -> str:
    """Genera el siguiente ID de sesión para un día, contando todas las sesiones iniciadas."""
    counter = 0
    for entry in read_json_lines(sessions_path):
        session = entry.get("session", {})
        event_type = entry.get("type")
        # Contar tanto SessionStarted como SessionStartedAfterDayClosed
        if session.get("day_id") == day_id and event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            counter += 1
    return f"S{counter + 1:02d}"


def current_session(
    events_path: Path, repo_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """Retorna la sesión actual (activa o paused) para un repo específico o global."""
    sessions: dict[str, dict[str, Any]] = {}
    for event in read_json_lines(events_path):
        event_type = event.get("type")
        # Manejar tanto SessionStarted como SessionStartedAfterDayClosed
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event["session"]["session_id"]
            sessions[session_id] = {
                "started": event,
                "ended": None,
                "paused": None,
                "resumed": None,
            }
        if event_type == "SessionEnded":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["ended"] = event
        if event_type == "SessionPaused":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["paused"] = event
                sessions[session_id]["resumed"] = None  # Reset resumed cuando se pausa
        if event_type == "SessionResumed":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["resumed"] = event
    
    for session_id in reversed(list(sessions.keys())):
        entry = sessions[session_id]
        if entry["ended"] is None:  # Sesión no terminada
            if repo_path:
                repo = entry["started"].get("repo") or {}
                if repo.get("path") != repo_path:
                    continue
            return entry["started"]
    return None


def active_session(
    events_path: Path, repo_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """Retorna la sesión activa (no paused) para un repo específico o global.
    
    Una sesión está activa si:
    - Tiene SessionStarted/SessionStartedAfterDayClosed
    - No tiene SessionEnded
    - No tiene SessionPaused, o tiene SessionPaused pero también tiene SessionResumed más reciente
    """
    sessions: dict[str, dict[str, Any]] = {}
    for event in read_json_lines(events_path):
        event_type = event.get("type")
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event["session"]["session_id"]
            sessions[session_id] = {
                "started": event,
                "ended": None,
                "paused": None,
                "resumed": None,
            }
        if event_type == "SessionEnded":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["ended"] = event
        if event_type == "SessionPaused":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["paused"] = event
        if event_type == "SessionResumed":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["resumed"] = event
    
    for session_id in reversed(list(sessions.keys())):
        entry = sessions[session_id]
        if entry["ended"] is None:  # Sesión no terminada
            # Verificar si está paused (tiene pause pero no resume más reciente)
            if entry["paused"]:
                if not entry["resumed"]:
                    # Está paused, no es activa
                    continue
                # Tiene resume, verificar que resume sea más reciente que pause
                paused_ts = entry["paused"].get("ts", "")
                resumed_ts = entry["resumed"].get("ts", "")
                if paused_ts > resumed_ts:
                    # Pause es más reciente, está paused
                    continue
            
            if repo_path:
                repo = entry["started"].get("repo") or {}
                if repo.get("path") != repo_path:
                    continue
            return entry["started"]
    return None
