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
        # Manejar tanto SessionStarted como SessionStartedAfterDayClosed
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
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
                "actor": event.get("actor"),
                "started_after_close": event_type == "SessionStartedAfterDayClosed",
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


def _summaries_path() -> Path:
    """Ruta al índice de resúmenes (summaries.ndjson)."""
    summaries_path = Path(settings.DATA_ROOT) / "index" / "summaries.ndjson"
    # Mantener compatibilidad temporal con daily_summaries.ndjson
    daily_summaries_path = Path(settings.DATA_ROOT) / "index" / "daily_summaries.ndjson"
    if summaries_path.exists():
        return summaries_path
    elif daily_summaries_path.exists():
        return daily_summaries_path
    return summaries_path


def _read_summaries() -> list[dict[str, Any]]:
    """Lee todos los resúmenes del índice."""
    path = _summaries_path()
    if not path.exists():
        return []
    summaries: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            summaries.append(json.loads(line))
    return summaries


def daily_summaries(request):
    """Retorna resúmenes con filtros opcionales."""
    summaries = _read_summaries()
    
    # Filtros
    day_id_filter = request.GET.get("day_id")
    mode_filter = request.GET.get("mode")
    limit = request.GET.get("limit")
    
    # Filtrar por día
    if day_id_filter:
        summaries = [
            s for s in summaries
            if s.get("session", {}).get("day_id") == day_id_filter
        ]
    
    # Filtrar por modo
    if mode_filter:
        summaries = [
            s for s in summaries
            if s.get("payload", {}).get("mode") == mode_filter
        ]
    
    # Ordenar y limitar
    summaries.sort(key=lambda s: s.get("ts", ""), reverse=True)
    
    if limit:
        summaries = summaries[:int(limit)]
    
    return JsonResponse({"summaries": summaries})


def summaries_latest(request):
    """Retorna el último resumen rolling del día especificado."""
    day_id_filter = request.GET.get("day_id")
    mode_filter = request.GET.get("mode", "rolling")
    
    if not day_id_filter:
        return JsonResponse({"error": "day_id requerido"}, status=400)
    
    summaries = _read_summaries()
    
    # Filtrar por día y modo
    filtered = [
        s for s in summaries
        if s.get("session", {}).get("day_id") == day_id_filter
        and s.get("payload", {}).get("mode") == mode_filter
    ]
    
    if not filtered:
        return JsonResponse({"summary": None})
    
    # Ordenar por timestamp y retornar el más reciente
    filtered.sort(key=lambda s: s.get("ts", ""), reverse=True)
    return JsonResponse({"summary": filtered[0]})


def day_closed(request):
    """Retorna si el día está cerrado (busca evento DayClosed)."""
    day_id_filter = request.GET.get("day_id")
    
    if not day_id_filter:
        return JsonResponse({"error": "day_id requerido"}, status=400)
    
    events = _read_events()
    
    # Buscar evento DayClosed para el día
    day_closed_events = [
        e for e in events
        if e.get("type") == "DayClosed"
        and e.get("session", {}).get("day_id") == day_id_filter
    ]
    
    is_closed = len(day_closed_events) > 0
    closed_event = day_closed_events[0] if day_closed_events else None
    
    return JsonResponse({
        "day_id": day_id_filter,
        "closed": is_closed,
        "closed_at": closed_event.get("payload", {}).get("closed_at") if closed_event else None,
    })


def day_today(request):
    """Retorna información del día actual: sesiones, estado, etc."""
    from datetime import datetime
    
    day_id_val = datetime.now().astimezone().date().isoformat()
    events = _read_events()
    
    # Filtrar eventos del día
    day_events = [
        e for e in events
        if e.get("session", {}).get("day_id") == day_id_val
    ]
    
    # Contar sesiones iniciadas (incluyendo SessionStartedAfterDayClosed)
    sessions_started = [
        e for e in day_events
        if e.get("type") in ("SessionStarted", "SessionStartedAfterDayClosed")
    ]
    
    # Construir lista de sesiones del día con start/end/elapsed
    sessions_today = []
    sessions_dict = {}
    
    for event in day_events:
        event_type = event.get("type")
        session_id = event.get("session", {}).get("session_id")
        
        # Manejar tanto SessionStarted como SessionStartedAfterDayClosed
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            if session_id not in sessions_dict:
                sessions_dict[session_id] = {
                    "session_id": session_id,
                    "start_ts": event.get("ts"),
                    "end_ts": None,
                    "intent": event.get("session", {}).get("intent"),
                    "dod": event.get("session", {}).get("dod"),
                    "repo": event.get("repo"),
                    "started_after_close": event_type == "SessionStartedAfterDayClosed",
                }
        elif event_type == "SessionEnded":
            if session_id in sessions_dict:
                sessions_dict[session_id]["end_ts"] = event.get("ts")
    
    # Calcular elapsed para cada sesión
    for session_id, session_data in sessions_dict.items():
        start_ts = session_data["start_ts"]
        end_ts = session_data["end_ts"]
        
        elapsed_minutes = None
        if start_ts:
            try:
                from datetime import datetime as dt
                start_dt = dt.fromisoformat(start_ts.replace("Z", "+00:00"))
                if end_ts:
                    end_dt = dt.fromisoformat(end_ts.replace("Z", "+00:00"))
                    delta = end_dt - start_dt
                    elapsed_minutes = int(delta.total_seconds() / 60)
                else:
                    # Sesión activa: calcular hasta ahora
                    now_dt = dt.now(start_dt.tzinfo)
                    delta = now_dt - start_dt
                    elapsed_minutes = int(delta.total_seconds() / 60)
            except Exception:
                pass
        
        sessions_today.append({
            **session_data,
            "elapsed_minutes": elapsed_minutes,
            "active": end_ts is None,
        })
    
    # Ordenar por start_ts descendente
    sessions_today.sort(key=lambda s: s.get("start_ts") or "", reverse=True)
    
    # Verificar si el día está cerrado
    day_closed_events = [
        e for e in day_events
        if e.get("type") == "DayClosed"
    ]
    is_closed = len(day_closed_events) > 0
    
    return JsonResponse({
        "day_id": day_id_val,
        "sessions_count": len(sessions_started),
        "sessions": sessions_today,
        "closed": is_closed,
        "closed_at": day_closed_events[0].get("payload", {}).get("closed_at") if day_closed_events else None,
    })


def jornada(request, day_id: str):
    """Retorna contenido de bitácora de jornada específica."""
    jornada_path = Path(settings.DATA_ROOT) / "bitacora" / f"{day_id}.md"
    if not jornada_path.exists():
        return JsonResponse({"error": "Jornada no encontrada"}, status=404)
    
    content = jornada_path.read_text(encoding="utf-8")
    return JsonResponse({"day_id": day_id, "content": content})


def captures_recent(request):
    """Retorna capturas recientes (CaptureCreated y CaptureReoccurred)."""
    limit = int(request.GET.get("limit", "20"))
    events = _read_events()
    
    captures = []
    for event in events:
        if event.get("type") in ("CaptureCreated", "CaptureReoccurred"):
            captures.append({
                "event_id": event.get("event_id"),
                "type": event.get("type"),
                "ts": event.get("ts"),
                "session": event.get("session"),
                "payload": event.get("payload", {}),
                "links": event.get("links", []),
            })
    
    captures.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return JsonResponse({"captures": captures[:limit]})


def errors_open(request):
    """Retorna lista de errores sin fix (último CaptureCreated sin FixLinked por sesión)."""
    events = _read_events()
    
    # Recopilar todos los CaptureCreated
    captures: dict[str, dict[str, Any]] = {}
    for event in events:
        if event.get("type") == "CaptureCreated":
            error_hash = event.get("payload", {}).get("error_hash")
            if error_hash:
                session_id = event.get("session", {}).get("session_id")
                if session_id:
                    key = f"{session_id}:{error_hash}"
                    captures[key] = event
    
    # Recopilar todos los FixLinked usando error_event_id (más preciso que error_hash)
    fixed_event_ids: set[str] = set()
    for event in events:
        if event.get("type") == "FixLinked":
            error_event_id = event.get("payload", {}).get("error_event_id")
            if error_event_id:
                fixed_event_ids.add(error_event_id)
    
    # Encontrar errores sin fix (último por sesión)
    open_errors: dict[str, dict[str, Any]] = {}
    for key, capture in captures.items():
        capture_event_id = capture.get("event_id")
        session_id = capture.get("session", {}).get("session_id")
        
        # Un error está fijado si tiene un FixLinked asociado a su event_id específico
        if capture_event_id not in fixed_event_ids:
            # Si ya hay un error abierto para esta sesión, mantener el más reciente
            if session_id not in open_errors:
                open_errors[session_id] = capture
            else:
                existing_ts = open_errors[session_id].get("ts", "")
                current_ts = capture.get("ts", "")
                if current_ts > existing_ts:
                    open_errors[session_id] = capture
    
    # Convertir a lista y formatear
    result = []
    for capture in open_errors.values():
        result.append({
            "event_id": capture.get("event_id"),
            "ts": capture.get("ts"),
            "session": capture.get("session"),
            "title": capture.get("payload", {}).get("title"),
            "error_hash": capture.get("payload", {}).get("error_hash"),
            "artifact_ref": capture.get("payload", {}).get("artifact_ref"),
            "links": capture.get("links", []),
        })
    
    result.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return JsonResponse({"errors": result})


def summaries_list(request, day_id: str):
    """Lista resúmenes disponibles para un día específico."""
    summaries_dir = Path(settings.DATA_ROOT) / "artifacts" / "summaries" / day_id
    if not summaries_dir.exists():
        return JsonResponse({"summaries": []})
    
    summaries = []
    for file_path in summaries_dir.glob("*.md"):
        summary_id = file_path.stem
        json_path = summaries_dir / f"{summary_id}.json"
        
        # Leer metadatos del JSON si existe
        metadata = {}
        if json_path.exists():
            try:
                metadata = json.loads(json_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        
        # Extraer modo del nombre del archivo o de los metadatos
        mode = "rolling" if summary_id.startswith("rolling_") else "nightly"
        if "mode" in metadata:
            mode = metadata.get("mode", mode)
        
        summaries.append({
            "summary_id": summary_id,
            "mode": mode,
            "timestamp": summary_id.split("_")[-1] if "_" in summary_id else "",
            "assessment": metadata.get("assessment", "UNKNOWN"),
            "ts": metadata.get("window_end", ""),
        })
    
    summaries.sort(key=lambda s: s.get("timestamp", ""), reverse=True)
    return JsonResponse({"summaries": summaries})


def summary_content(request, day_id: str, summary_id: str):
    """Devuelve contenido markdown de un resumen específico."""
    summary_path = Path(settings.DATA_ROOT) / "artifacts" / "summaries" / day_id / f"{summary_id}.md"
    if not summary_path.exists():
        return JsonResponse({"error": "Resumen no encontrado"}, status=404)
    
    content = summary_path.read_text(encoding="utf-8")
    return JsonResponse({"day_id": day_id, "summary_id": summary_id, "content": content})


def _build_docs_tree(docs_dir: Path, base_path: Path) -> list[dict[str, Any]]:
    """Construye árbol de documentación recursivamente."""
    tree = []
    
    if not docs_dir.exists():
        return tree
    
    # Ordenar: directorios primero, luego archivos
    items = sorted(docs_dir.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    
    for item in items:
        # Ignorar archivos ocultos y no-markdown
        if item.name.startswith("."):
            continue
        
        if item.is_dir():
            children = _build_docs_tree(item, base_path)
            tree.append({
                "name": item.name,
                "type": "directory",
                "path": str(item.relative_to(base_path)),
                "children": children,
            })
        elif item.suffix == ".md":
            tree.append({
                "name": item.name,
                "type": "file",
                "path": str(item.relative_to(base_path)),
            })
    
    return tree


def docs_list(request):
    """Lista estructura de documentación (árbol recursivo)."""
    # docs/ está montado directamente en /docs en el contenedor
    docs_dir = Path("/docs")
    
    if not docs_dir.exists():
        return JsonResponse({"tree": []})
    
    tree = _build_docs_tree(docs_dir, docs_dir)
    return JsonResponse({"tree": tree})


def doc_content(request, doc_path: str):
    """Devuelve contenido markdown de un documento."""
    # docs/ está montado directamente en /docs en el contenedor
    docs_dir = Path("/docs")
    doc_file = docs_dir / doc_path
    
    # Validar que el archivo está dentro de docs/ (seguridad)
    try:
        doc_file.resolve().relative_to(docs_dir.resolve())
    except ValueError:
        return JsonResponse({"error": "Ruta inválida"}, status=400)
    
    if not doc_file.exists() or not doc_file.is_file():
        return JsonResponse({"error": "Documento no encontrado"}, status=404)
    
    if doc_file.suffix != ".md":
        return JsonResponse({"error": "Solo se permiten archivos .md"}, status=400)
    
    content = doc_file.read_text(encoding="utf-8")
    return JsonResponse({"path": doc_path, "content": content})
