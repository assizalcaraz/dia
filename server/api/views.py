import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from django.conf import settings
from django.http import JsonResponse


def _events_path() -> Path:
    return Path(settings.DATA_ROOT) / "index" / "events.ndjson"


def _sessions_path() -> Path:
    return Path(settings.DATA_ROOT) / "index" / "sessions.ndjson"


def _event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def _now_iso() -> str:
    """Retorna timestamp ISO 8601 con timezone."""
    return datetime.now().astimezone().isoformat()


def _append_line(path: Path, data: dict[str, Any]) -> None:
    """Añade una línea JSON al archivo NDJSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


def _build_event(
    event_type: str,
    session: dict[str, Any],
    actor: dict[str, Any],
    project: dict[str, Any],
    repo: dict[str, Any] | None,
    payload: dict[str, Any] | None = None,
    links: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Construye un evento en formato NDJSON."""
    return {
        "event_id": _event_id(),
        "ts": _now_iso(),
        "type": event_type,
        "session": session,
        "actor": actor,
        "project": project,
        "repo": repo,
        "payload": payload or {},
        "links": links or [],
    }


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
                "paused_ts": None,
                "resumed_ts": None,
            }
        if event_type == "SessionEnded":
            session = event.get("session", {})
            session_id = session.get("session_id")
            if not session_id or session_id not in sessions:
                continue
            sessions[session_id]["end_ts"] = event.get("ts")
            sessions[session_id]["result"] = session.get("result")
            sessions[session_id]["repo"] = event.get("repo")
        if event_type == "SessionPaused":
            session = event.get("session", {})
            session_id = session.get("session_id")
            if session_id and session_id in sessions:
                sessions[session_id]["paused_ts"] = event.get("ts")
        if event_type == "SessionResumed":
            session = event.get("session", {})
            session_id = session.get("session_id")
            if session_id and session_id in sessions:
                sessions[session_id]["resumed_ts"] = event.get("ts")
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


def active_session(request):
    """Retorna la sesión activa (no paused) o None.
    
    Una sesión está activa si:
    - Tiene SessionStarted/SessionStartedAfterDayClosed
    - No tiene SessionEnded ni SessionForceClosed
    - No tiene SessionPaused, o tiene SessionPaused pero también tiene SessionResumed más reciente
    
    Si hay múltiples sesiones activas, retorna la más reciente y agrega advertencia.
    Si hay sesión sin end_ts y day_id != today, la marca como anomalía pero no la oculta.
    """
    from datetime import datetime
    
    events = _read_events()
    sessions: dict[str, dict[str, Any]] = {}
    ended_sessions: set[str] = set()  # Track sessions that have ended (key: session_id:repo_path)
    today = datetime.now().astimezone().date().isoformat()
    anomalies: list[dict[str, Any]] = []
    
    # Primero, identificar todas las sesiones que han terminado
    # Usar clave compuesta session_id:repo_path para distinguir sesiones en diferentes repos
    for event in events:
        if event.get("type") in ("SessionEnded", "SessionForceClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            if session_id:
                # Clave compuesta para distinguir sesiones en diferentes repos
                key = f"{session_id}:{repo_path}"
                ended_sessions.add(key)
    
    # Ahora construir sesiones y verificar estado
    for event in events:
        event_type = event.get("type")
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event.get("session", {}).get("session_id")
            if not session_id:
                continue
            repo_path = event.get("repo", {}).get("path", "")
            # Clave compuesta para distinguir sesiones en diferentes repos
            key = f"{session_id}:{repo_path}"
            # Solo procesar si la sesión no ha terminado
            if key not in ended_sessions:
                day_id = event.get("session", {}).get("day_id")
                session_data = {
                    "day_id": day_id,
                    "session_id": session_id,
                    "intent": event.get("session", {}).get("intent"),
                    "dod": event.get("session", {}).get("dod"),
                    "mode": event.get("session", {}).get("mode"),
                    "start_ts": event.get("ts"),
                    "end_ts": None,
                    "result": None,
                    "repo": event.get("repo"),
                    "project": event.get("project"),
                    "actor": event.get("actor"),
                    "started_after_close": event_type == "SessionStartedAfterDayClosed",
                    "paused_ts": None,
                    "resumed_ts": None,
                }
                sessions[key] = session_data
                
                # Detectar anomalía: sesión vieja sin cerrar
                if day_id != today:
                    anomalies.append({
                        "session_id": session_id,
                        "day_id": day_id,
                        "type": "orphan_old_session",
                    })
        if event_type == "SessionPaused":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions:
                sessions[key]["paused_ts"] = event.get("ts")
        if event_type == "SessionResumed":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions:
                sessions[key]["resumed_ts"] = event.get("ts")
    
    # Buscar sesión activa (no ended, no paused o resumed después de paused)
    sessions_list = list(sessions.values())
    sessions_list.sort(key=lambda item: item.get("start_ts") or "", reverse=True)
    
    active_sessions = []
    for item in sessions_list:
        # Verificar explícitamente que no esté en ended_sessions usando clave compuesta
        session_id = item.get("session_id")
        repo_path = item.get("repo", {}).get("path", "")
        key = f"{session_id}:{repo_path}"
        if key in ended_sessions:
            continue
            
        paused_ts = item.get("paused_ts")
        resumed_ts = item.get("resumed_ts")
        
        # Verificar estado paused
        is_paused = False
        if paused_ts:
            if not resumed_ts:
                is_paused = True
            elif paused_ts > resumed_ts:
                is_paused = True
        
        # Si no está paused, es activa
        if not is_paused:
            active_sessions.append(item)
    
    # Si hay múltiples activas, retornar la más reciente y agregar advertencia
    if len(active_sessions) > 1:
        # Registrar anomalía
        anomalies.append({
            "type": "multiple_active_sessions",
            "count": len(active_sessions),
            "sessions": [s["session_id"] for s in active_sessions],
        })
        # Retornar la más reciente
        response = {"session": active_sessions[0]}
        if anomalies:
            response["anomalies"] = anomalies
        return JsonResponse(response)
    
    # Si hay una activa, retornarla (con advertencias si aplica)
    if active_sessions:
        response = {"session": active_sessions[0]}
        if anomalies:
            response["anomalies"] = anomalies
        return JsonResponse(response)
    
    # No hay sesiones activas
    response = {"session": None}
    if anomalies:
        response["anomalies"] = anomalies
    return JsonResponse(response)


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


def jornada_human_update(request, day_id: str):
    """Actualiza solo las secciones humanas (1 y 2) de la bitácora."""
    from datetime import datetime
    import json
    
    # Validar que es día actual
    today = datetime.now().astimezone().date().isoformat()
    if day_id != today:
        return JsonResponse(
            {"error": "Solo se puede editar la bitácora del día actual"},
            status=403
        )
    
    if request.method != "PUT":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    try:
        data = json.loads(request.body)
        new_human_content = data.get("content", "").strip()
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({"error": "Datos inválidos"}, status=400)
    
    jornada_path = Path(settings.DATA_ROOT) / "bitacora" / f"{day_id}.md"
    
    # Leer contenido existente
    if jornada_path.exists():
        existing_content = jornada_path.read_text(encoding="utf-8")
        
        # Separar secciones humanas y automáticas
        separator = "---\n\n## 3. Registro automático (NO EDITAR)"
        separator_index = existing_content.find(separator)
        
        if separator_index != -1:
            # Hay sección automática, preservarla
            auto_section = existing_content[separator_index:]
            # Reconstruir con nuevas secciones humanas
            new_content = new_human_content + "\n\n" + auto_section
        else:
            # No hay sección automática aún, solo actualizar humanas
            new_content = new_human_content
    else:
        # No existe, crear nueva con template básico
        # Si hay contenido humano, usarlo; si no, crear estructura básica
        if new_human_content:
            new_content = new_human_content
        else:
            # Crear estructura básica
            new_content = (
                f"# Jornada {day_id}\n\n"
                "## 1. Intención del día (manual)\n"
                "- Objetivo principal:\n"
                "- Definición de Hecho (DoD):\n"
                "- Restricciones / contexto:\n\n"
                "## 2. Notas humanas (manual)\n"
                "- ideas\n"
                "- dudas\n"
                "- decisiones\n"
                "- observaciones subjetivas relevantes\n\n"
                "---\n\n"
                "## 3. Registro automático (NO EDITAR)\n"
                "(append-only, escrito por /dia)\n\n"
            )
    
    # Validar que no se intentó modificar el separador
    if "---\n\n## 3. Registro automático (NO EDITAR)" in new_human_content:
        return JsonResponse(
            {"error": "No se puede modificar el separador de secciones"},
            status=400
        )
    
    # Escribir archivo
    try:
        jornada_path.parent.mkdir(parents=True, exist_ok=True)
        jornada_path.write_text(new_content, encoding="utf-8")
        return JsonResponse({"day_id": day_id, "status": "updated"})
    except Exception as e:
        return JsonResponse({"error": f"Error al escribir archivo: {str(e)}"}, status=500)


def notes_tmp_list(request, day_id: str):
    """Lista archivos temporales del día."""
    notes_dir = Path(settings.DATA_ROOT) / "notes" / "tmp" / day_id
    if not notes_dir.exists():
        return JsonResponse({"day_id": day_id, "files": []})
    
    files = []
    for md_file in notes_dir.glob("*.md"):
        stat = md_file.stat()
        files.append({
            "name": md_file.name,
            "path": str(md_file.relative_to(Path(settings.DATA_ROOT))),
            "size": stat.st_size,
            "modified": stat.st_mtime,
        })
    
    # Ordenar por fecha de modificación (más reciente primero)
    files.sort(key=lambda f: f["modified"], reverse=True)
    
    return JsonResponse({"day_id": day_id, "files": files})


def notes_tmp_content(request, day_id: str, file_name: str):
    """Retorna contenido de un archivo temporal."""
    # Validar que el nombre del archivo no contenga path traversal
    if ".." in file_name or "/" in file_name or "\\" in file_name:
        return JsonResponse({"error": "Nombre de archivo inválido"}, status=400)
    
    notes_dir = Path(settings.DATA_ROOT) / "notes" / "tmp" / day_id
    file_path = notes_dir / file_name
    
    if not file_path.exists():
        return JsonResponse({"error": "Archivo no encontrado"}, status=404)
    
    # Validar que el archivo está dentro del directorio esperado
    try:
        file_path.resolve().relative_to(notes_dir.resolve())
    except ValueError:
        return JsonResponse({"error": "Ruta inválida"}, status=400)
    
    try:
        content = file_path.read_text(encoding="utf-8")
        return JsonResponse({"day_id": day_id, "file_name": file_name, "content": content})
    except Exception as e:
        return JsonResponse({"error": f"Error al leer archivo: {str(e)}"}, status=500)


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
        capture_event_id = capture.get("event_id")
        has_fix = capture_event_id in fixed_event_ids
        result.append({
            "event_id": capture_event_id,
            "ts": capture.get("ts"),
            "session": capture.get("session"),
            "title": capture.get("payload", {}).get("title"),
            "error_hash": capture.get("payload", {}).get("error_hash"),
            "artifact_ref": capture.get("payload", {}).get("artifact_ref"),
            "links": capture.get("links", []),
            "has_fix": has_fix,
        })
    
    result.sort(key=lambda x: x.get("ts", ""), reverse=True)
    return JsonResponse({"errors": result})


def chain_latest(request):
    """Retorna la última cadena abierta Error→Fix→Commit de la sesión actual."""
    events = _read_events()
    
    # Encontrar sesión activa
    sessions_list = _build_sessions(events)
    sessions_list.sort(key=lambda item: item.get("start_ts") or "", reverse=True)
    current_session_data = None
    for item in sessions_list:
        if item.get("end_ts") is None:
            current_session_data = item
            break
    
    if not current_session_data:
        return JsonResponse({"error": None, "fix": None, "commit": None})
    
    session_id = current_session_data.get("session_id")
    
    # Buscar último error sin fix (CaptureCreated)
    captures = []
    for event in events:
        if event.get("type") == "CaptureCreated":
            event_session_id = event.get("session", {}).get("session_id")
            if event_session_id == session_id:
                captures.append(event)
    
    if not captures:
        return JsonResponse({"error": None, "fix": None, "commit": None})
    
    # Ordenar por timestamp y tomar el más reciente
    captures.sort(key=lambda x: x.get("ts", ""), reverse=True)
    latest_capture = captures[0]
    error_event_id = latest_capture.get("event_id")
    
    # Buscar FixLinked asociado
    fix_linked = None
    for event in events:
        if event.get("type") == "FixLinked":
            if event.get("payload", {}).get("error_event_id") == error_event_id:
                fix_linked = event
                break
    
    # Buscar FixCommitted asociado
    fix_committed = None
    if fix_linked:
        fix_event_id = fix_linked.get("event_id")
        for event in events:
            if event.get("type") == "FixCommitted":
                if event.get("payload", {}).get("fix_event_id") == fix_event_id:
                    fix_committed = event
                    break
    
    # Construir respuesta
    result = {
        "error": {
            "event_id": latest_capture.get("event_id"),
            "ts": latest_capture.get("ts"),
            "title": latest_capture.get("payload", {}).get("title"),
            "error_hash": latest_capture.get("payload", {}).get("error_hash"),
            "artifact_ref": latest_capture.get("payload", {}).get("artifact_ref"),
        } if latest_capture else None,
        "fix": {
            "fix_id": fix_linked.get("payload", {}).get("fix_id"),
            "event_id": fix_linked.get("event_id"),
            "ts": fix_linked.get("ts"),
            "title": fix_linked.get("payload", {}).get("title"),
            "fix_sha": fix_linked.get("payload", {}).get("fix_sha"),
        } if fix_linked else None,
        "commit": {
            "commit_sha": fix_committed.get("payload", {}).get("commit_sha"),
            "event_id": fix_committed.get("event_id"),
            "ts": fix_committed.get("ts"),
        } if fix_committed else None,
    }
    
    return JsonResponse(result)


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


def endpoints_doc(request):
    """Endpoint para /api/endpoints.md - retorna la documentación de endpoints."""
    # Usar el mismo endpoint que doc_content pero con la ruta fija
    doc_path = "modules/api/endpoints.md"
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


def session_pause(request):
    """Pausa la sesión activa actual."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    events = _read_events()
    events_path = _events_path()
    sessions_path = _sessions_path()
    
    # Importar funciones de sesión del CLI (necesitamos importarlas o replicar lógica)
    # Por ahora, replicamos la lógica básica
    from datetime import datetime as dt
    today = dt.now().astimezone().date().isoformat()
    
    # Buscar sesión activa (no paused, no ended)
    active_session_data = None
    sessions_dict = {}
    ended_sessions = set()
    
    for event in events:
        event_type = event.get("type")
        if event_type in ("SessionEnded", "SessionForceClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            if session_id:
                ended_sessions.add(f"{session_id}:{repo_path}")
        
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key not in ended_sessions:
                sessions_dict[key] = {
                    "session_id": session_id,
                    "day_id": event.get("session", {}).get("day_id"),
                    "start_ts": event.get("ts"),
                    "paused_ts": None,
                    "resumed_ts": None,
                    "repo": event.get("repo"),
                }
        
        if event_type == "SessionPaused":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions_dict:
                sessions_dict[key]["paused_ts"] = event.get("ts")
        
        if event_type == "SessionResumed":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions_dict:
                sessions_dict[key]["resumed_ts"] = event.get("ts")
    
    # Encontrar sesión activa (no ended, no paused o resumed después de paused)
    for key, session_data in sessions_dict.items():
        if key in ended_sessions:
            continue
        paused_ts = session_data.get("paused_ts")
        resumed_ts = session_data.get("resumed_ts")
        is_paused = False
        if paused_ts:
            if not resumed_ts:
                is_paused = True
            elif paused_ts > resumed_ts:
                is_paused = True
        if not is_paused:
            active_session_data = session_data
            break
    
    if not active_session_data:
        return JsonResponse({"error": "No hay sesión activa"}, status=400)
    
    session_id = active_session_data["session_id"]
    day_id_val = active_session_data["day_id"]
    
    # Crear evento SessionPaused
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    }
    
    pause_event = _build_event(
        "SessionPaused",
        session=session,
        actor={
            "user_id": "u_web",
            "user_type": "human",
            "role": "desarrollador",
            "client": "web",
        },
        project={"tag": None, "area": "it", "context": ""},
        repo=active_session_data.get("repo"),
        payload={
            "cmd": "web pause",
            "reason": None,
        },
    )
    
    _append_line(events_path, pause_event)
    _append_line(sessions_path, pause_event)
    
    return JsonResponse({"status": "paused", "session_id": session_id})


def session_resume(request):
    """Reanuda una sesión pausada."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    events = _read_events()
    events_path = _events_path()
    sessions_path = _sessions_path()
    
    # Buscar sesión pausada (no ended, paused sin resume más reciente)
    paused_session_data = None
    sessions_dict = {}
    ended_sessions = set()
    
    for event in events:
        event_type = event.get("type")
        if event_type in ("SessionEnded", "SessionForceClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            if session_id:
                ended_sessions.add(f"{session_id}:{repo_path}")
        
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key not in ended_sessions:
                sessions_dict[key] = {
                    "session_id": session_id,
                    "day_id": event.get("session", {}).get("day_id"),
                    "start_ts": event.get("ts"),
                    "paused_ts": None,
                    "resumed_ts": None,
                    "repo": event.get("repo"),
                }
        
        if event_type == "SessionPaused":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions_dict:
                sessions_dict[key]["paused_ts"] = event.get("ts")
        
        if event_type == "SessionResumed":
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key in sessions_dict:
                sessions_dict[key]["resumed_ts"] = event.get("ts")
    
    # Encontrar sesión pausada
    for key, session_data in sessions_dict.items():
        if key in ended_sessions:
            continue
        paused_ts = session_data.get("paused_ts")
        resumed_ts = session_data.get("resumed_ts")
        is_paused = False
        if paused_ts:
            if not resumed_ts:
                is_paused = True
            elif paused_ts > resumed_ts:
                is_paused = True
        if is_paused:
            paused_session_data = session_data
            break
    
    if not paused_session_data:
        return JsonResponse({"error": "No hay sesión pausada"}, status=400)
    
    session_id = paused_session_data["session_id"]
    day_id_val = paused_session_data["day_id"]
    
    # Crear evento SessionResumed
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    }
    
    resume_event = _build_event(
        "SessionResumed",
        session=session,
        actor={
            "user_id": "u_web",
            "user_type": "human",
            "role": "desarrollador",
            "client": "web",
        },
        project={"tag": None, "area": "it", "context": ""},
        repo=paused_session_data.get("repo"),
        payload={
            "cmd": "web resume",
        },
    )
    
    _append_line(events_path, resume_event)
    _append_line(sessions_path, resume_event)
    
    return JsonResponse({"status": "resumed", "session_id": session_id})


def session_end(request):
    """Finaliza la sesión activa actual."""
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)
    
    events = _read_events()
    events_path = _events_path()
    sessions_path = _sessions_path()
    
    # Buscar sesión activa o pausada (no ended)
    current_session_data = None
    sessions_dict = {}
    ended_sessions = set()
    
    for event in events:
        event_type = event.get("type")
        if event_type in ("SessionEnded", "SessionForceClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            if session_id:
                ended_sessions.add(f"{session_id}:{repo_path}")
        
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event.get("session", {}).get("session_id")
            repo_path = event.get("repo", {}).get("path", "")
            key = f"{session_id}:{repo_path}"
            if key not in ended_sessions:
                sessions_dict[key] = {
                    "session_id": session_id,
                    "day_id": event.get("session", {}).get("day_id"),
                    "start_ts": event.get("ts"),
                    "paused_ts": None,
                    "resumed_ts": None,
                    "repo": event.get("repo"),
                }
    
    # Encontrar sesión actual (no ended)
    for key, session_data in sessions_dict.items():
        if key not in ended_sessions:
            current_session_data = session_data
            break
    
    if not current_session_data:
        return JsonResponse({"error": "No hay sesión activa o pausada"}, status=400)
    
    session_id = current_session_data["session_id"]
    day_id_val = current_session_data["day_id"]
    
    # Crear evento SessionEnded
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
        "result": None,
    }
    
    end_event = _build_event(
        "SessionEnded",
        session=session,
        actor={
            "user_id": "u_web",
            "user_type": "human",
            "role": "desarrollador",
            "client": "web",
        },
        project={"tag": None, "area": "it", "context": ""},
        repo=current_session_data.get("repo"),
        payload={
            "cmd": "web end",
        },
    )
    
    _append_line(events_path, end_event)
    _append_line(sessions_path, end_event)
    
    return JsonResponse({"status": "ended", "session_id": session_id})
