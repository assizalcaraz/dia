import json
from pathlib import Path
from typing import Any

from django.conf import settings
from django.http import JsonResponse


def _events_path() -> Path:
    return Path(settings.DATA_ROOT) / "index" / "events.ndjson"


def _read_events() -> list[dict[str, Any]]:
    path = _events_path()
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            events.append(json.loads(line))
    return events


def _build_sessions(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sessions: dict[str, dict[str, Any]] = {}
    for event in events:
        event_type = event.get("type")
        if event_type == "SessionStarted":
            session = event.get("session", {})
            session_id = session.get("session_id")
            if not session_id:
                continue
            sessions[session_id] = {
                "day_id": session.get("day_id"),
                "session_id": session_id,
                "intent": session.get("intent"),
                "dod": session.get("dod"),
                "mode": session.get("mode"),
                "start_ts": event.get("ts"),
                "end_ts": None,
                "result": None,
                "repo": event.get("repo"),
                "project": event.get("project"),
            }
        if event_type == "SessionEnded":
            session = event.get("session", {})
            session_id = session.get("session_id")
            if not session_id or session_id not in sessions:
                continue
            sessions[session_id]["end_ts"] = event.get("ts")
            sessions[session_id]["result"] = session.get("result")
            sessions[session_id]["repo"] = event.get("repo")
    return list(sessions.values())


def sessions(request):
    events = _read_events()
    items = _build_sessions(events)
    items.sort(key=lambda item: item.get("start_ts") or "", reverse=True)
    return JsonResponse({"sessions": items})


def current_session(request):
    events = _read_events()
    sessions_list = _build_sessions(events)
    sessions_list.sort(key=lambda item: item.get("start_ts") or "", reverse=True)
    for item in sessions_list:
        if item.get("end_ts") is None:
            return JsonResponse({"session": item})
    return JsonResponse({"session": None})


def events_recent(request):
    limit = int(request.GET.get("limit", "20"))
    events = _read_events()
    return JsonResponse({"events": events[-limit:]})


def metrics(request):
    events = _read_events()
    sessions_list = _build_sessions(events)
    commit_suggestions = [
        event for event in events if event.get("type") == "CommitSuggestionIssued"
    ]
    return JsonResponse(
        {
            "total_sessions": len(sessions_list),
            "commit_suggestions": len(commit_suggestions),
            "total_events": len(events),
        }
    )
