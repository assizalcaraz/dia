from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from .utils import read_json_lines


def next_session_id(day_id: str, sessions_path: Path) -> str:
    counter = 0
    for entry in read_json_lines(sessions_path):
        session = entry.get("session", {})
        if session.get("day_id") == day_id:
            counter += 1
    return f"S{counter + 1:02d}"


def current_session(
    events_path: Path, repo_path: Optional[str] = None
) -> Optional[dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    for event in read_json_lines(events_path):
        if event.get("type") == "SessionStarted":
            session_id = event["session"]["session_id"]
            sessions[session_id] = {
                "started": event,
                "ended": None,
            }
        if event.get("type") == "SessionEnded":
            session_id = event["session"]["session_id"]
            if session_id in sessions:
                sessions[session_id]["ended"] = event
    for session_id in reversed(list(sessions.keys())):
        entry = sessions[session_id]
        if entry["ended"] is None:
            if repo_path:
                repo = entry["started"].get("repo") or {}
                if repo.get("path") != repo_path:
                    continue
            return entry["started"]
    return None
