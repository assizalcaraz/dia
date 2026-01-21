from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path
import subprocess
from typing import Any, Optional

from . import config
from .config import captures_dir
from .cursor_reminder import write_reminder_to_file
from .git_ops import (
    changed_files,
    changed_files_working,
    current_branch,
    diff,
    empty_tree_sha,
    head_sha,
    is_git_repo,
    log_oneline,
    ls_tree,
    run_git,
    status_porcelain,
    tracked_files_count,
)
from .ndjson import append_line
from .rules import load_rules, load_repo_structure_rules
from .sessions import active_session, current_session, next_session_id
from .templates import cierre_template, limpieza_template, session_start_template
from .utils import (
    compute_content_hash,
    day_id,
    find_last_unfixed_capture,
    now_iso,
    read_json_lines,
    read_text,
    write_text,
)
from .llm_analyzer import analyze_error_with_llm


def _event_id() -> str:
    return f"evt_{uuid.uuid4().hex}"


def _build_event(
    event_type: str,
    session: dict[str, Any],
    actor: dict[str, Any],
    project: dict[str, Any],
    repo: Optional[dict[str, Any]],
    payload: Optional[dict[str, Any]] = None,
    links: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    return {
        "event_id": _event_id(),
        "ts": now_iso(),
        "type": event_type,
        "session": session,
        "actor": actor,
        "project": project,
        "repo": repo,
        "payload": payload or {},
        "links": links or [],
    }


def _actor_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "user_id": args.actor,
        "user_type": args.user_type,
        "role": args.role,
        "client": args.client,
    }


def _project_from_args(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "tag": args.project,
        "area": args.area,
        "context": args.context,
    }


def _session_payload(args: argparse.Namespace, session_id: str) -> dict[str, Any]:
    return {
        "day_id": day_id(),
        "session_id": session_id,
        "intent": args.intent,
        "dod": args.dod,
        "mode": args.mode,
    }


def _repo_payload(repo_path: Path, branch: str, start_sha: Optional[str]) -> dict[str, Any]:
    return {
        "path": str(repo_path),
        "vcs": "git",
        "branch": branch,
        "start_sha": start_sha,
        "end_sha": None,
        "dirty": bool(status_porcelain(repo_path)),
    }


def _events_path(root: Path) -> Path:
    return config.index_dir(root) / "events.ndjson"


def _sessions_path(root: Path) -> Path:
    return config.index_dir(root) / "sessions.ndjson"


def _write_bitacora_start(
    root: Path,
    day: str,
    session_id: str,
    intent: str,
    dod: str,
    mode: str,
    repo_path: str,
    branch: str,
    start_sha: str,
) -> Path:
    """Escribe inicio de sesión en bitácora de jornada (archivo único por día)."""
    from .templates import session_auto_section_template
    from .utils import append_to_jornada_auto_section
    
    # Archivo único por jornada: bitacora/YYYY-MM-DD.md
    jornada_path = config.bitacora_dir(root) / f"{day}.md"
    
    # Generar contenido de sesión para sección automática
    session_content = session_auto_section_template(
        session_id=session_id,
        start_ts=now_iso(),
        intent=intent,
        dod=dod,
        mode=mode,
        repo_path=str(repo_path),
        branch=branch,
        start_sha=start_sha or "None",
    )
    
    # Agregar evento inicial
    session_content += f"- {now_iso()} — SessionStarted\n"
    
    append_to_jornada_auto_section(jornada_path, session_content)
    return jornada_path


def _write_artifact(root: Path, filename: str, content: str) -> Path:
    path = config.artifacts_dir(root) / filename
    write_text(path, content)
    return path


def _suggest_commit_message(
    session_id: str, rules: dict[str, Any], files: list[str]
) -> str:
    if files and all(path.startswith("docs/") for path in files):
        commit_type = "docs"
    elif files and any(path.startswith("tests/") or "/tests/" in path for path in files):
        commit_type = "test"
    elif files:
        commit_type = "feat"
    else:
        commit_type = "chore"
    # 🦾 al inicio para identificación rápida en git log
    return f'🦾 {commit_type}: pre-feat checkpoint [#sesion {session_id}]'


def _cleanup_tasks(rules: dict[str, Any], files: list[str]) -> list[str]:
    tasks: list[str] = []
    for file_path in files:
        if file_path.startswith("docs/scratch/"):
            tasks.append(
                f"Mover {file_path} -> docs/_scratch/ (evitar drift)"
            )
        if file_path.endswith("_test.py") and "/tests/" not in file_path:
            tasks.append(
                f"Mover {file_path} a tests/test_<feature>.py"
            )
    if not tasks:
        tasks.append("Revisar cambios y consolidar docs si aplica")
    return tasks


def _analyze_error_simple(content: str) -> str:
    """Análisis simple de error cuando LLM no está disponible."""
    from .llm_analyzer import _analyze_simple
    return _analyze_simple(content, "error")


def cmd_session_start(args: argparse.Namespace) -> int:
    """Inicia una sesión. Crea day_id si no existe."""
    return cmd_start(args)


def cmd_session_end(args: argparse.Namespace) -> int:
    """Cierra la sesión activa. NO genera nightly automáticamente."""
    return cmd_end(args)


def cmd_session_pause(args: argparse.Namespace) -> int:
    """Pausa la sesión activa."""
    return cmd_pause(args)


def cmd_session_resume(args: argparse.Namespace) -> int:
    """Reanuda una sesión pausada."""
    return cmd_resume(args)


def cmd_session_close(args: argparse.Namespace) -> int:
    """Cierra una sesión por ID (reparación manual de sesiones huérfanas)."""
    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    sessions_path = _sessions_path(root)
    
    session_id = args.session_id
    if not session_id:
        print("Error: --id requerido", file=sys.stderr)
        return 1
    
    # Buscar sesión por ID en eventos
    events = list(read_json_lines(events_path))
    session_started = None
    session_ended = False
    
    for event in events:
        event_type = event.get("type")
        event_session_id = event.get("session", {}).get("session_id")
        
        if event_session_id == session_id:
            if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
                session_started = event
            elif event_type == "SessionEnded":
                session_ended = True
                break
    
    if not session_started:
        print(f"Error: Sesión {session_id} no encontrada.", file=sys.stderr)
        return 1
    
    if session_ended:
        print(f"Sesión {session_id} ya está cerrada.", file=sys.stderr)
        return 0
    
    # Crear evento SessionForceClosed
    session = {
        "day_id": session_started["session"]["day_id"],
        "session_id": session_id,
        "result": "forced_close",
    }
    
    close_event = _build_event(
        "SessionForceClosed",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=session_started.get("repo"),
        payload={
            "cmd": "dia session close",
            "reason": args.reason or "Sesión huérfana detectada y reparada",
            "forced": True,
        },
    )
    
    # También crear SessionEnded para compatibilidad
    end_event = _build_event(
        "SessionEnded",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=session_started.get("repo"),
        payload={
            "cmd": "dia session close",
            "forced": True,
            "duration_min": None,
        },
    )
    
    append_line(events_path, close_event)
    append_line(events_path, end_event)
    append_line(sessions_path, end_event)
    
    # Actualizar bitácora
    jornada_path = config.bitacora_dir(root) / f"{session['day_id']}.md"
    if jornada_path.exists():
        from .utils import append_to_jornada_auto_section
        reason_text = f" — {args.reason}" if args.reason else ""
        close_info = f"- {now_iso()} — SessionForceClosed{reason_text}\n"
        close_info += f"- {now_iso()} — SessionEnded (forced)\n"
        append_to_jornada_auto_section(jornada_path, close_info)
    
    print(f"Sesión {session_id} cerrada forzadamente. Eventos SessionForceClosed y SessionEnded registrados.")
    return 0


def cmd_start(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    project_name = args.project or repo_path.name
    print(f"Se usara '{project_name}' como nombre del proyecto.")
    confirm = input("Confirmar? (escriba 'no' para cancelar): ").strip().lower()
    if confirm in {"no", "n"}:
        print("Cancelado. Haga cd al repo correcto y reintente.")
        return 1
    if not is_git_repo(repo_path):
        print("Repo invalido o no es git.", file=sys.stderr)
        return 1

    if not args.project:
        args.project = project_name
    if not args.intent:
        args.intent = input("Intencion (1 frase): ").strip()
    if not args.dod:
        args.dod = input("Definicion de hecho (DoD): ").strip()
    if not args.mode:
        args.mode = input("Modo [it]: ").strip() or "it"

    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    sessions_path = _sessions_path(root)
    events_path = _events_path(root)

    # Validar que no haya sesión activa (no paused) para este repositorio
    active = active_session(events_path, repo_path=str(repo_path))
    if active:
        session_id_active = active.get("session", {}).get("session_id", "N/A")
        active_repo = active.get("repo", {}).get("path", "N/A")
        print(f"Error: Ya hay una sesión activa: {session_id_active}", file=sys.stderr)
        print(f"  Repositorio: {active_repo}", file=sys.stderr)
        print("Sugerencia: Ejecuta 'dia end' para cerrar la sesión activa o 'dia pause' para pausarla.", file=sys.stderr)
        return 1

    # Verificar si el día está cerrado
    current_day = day_id()
    events = list(read_json_lines(events_path))
    day_events = [e for e in events if e.get("session", {}).get("day_id") == current_day]
    day_closed = any(e.get("type") == "DayClosed" for e in day_events)

    session_id = next_session_id(current_day, sessions_path)
    actor = _actor_from_args(args)
    project = _project_from_args(args)

    branch = current_branch(repo_path)
    start_sha = head_sha(repo_path)
    if start_sha is None:
        print("Repo sin commits. Continuando en modo inicial.")
    repo_state = _repo_payload(repo_path, branch, start_sha)

    session = _session_payload(args, session_id)
    
    # Determinar tipo de evento según si el día está cerrado
    event_type = "SessionStartedAfterDayClosed" if day_closed else "SessionStarted"
    
    start_event = _build_event(
        event_type,
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={"cmd": "dia start", "day_was_closed": day_closed},
    )
    baseline_event = _build_event(
        "RepoBaselineCaptured",
        session={"day_id": session["day_id"], "session_id": session_id},
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "status_porcelain": status_porcelain(repo_path),
            "tracked_files": tracked_files_count(repo_path),
        },
    )
    if repo_state["dirty"]:
        diff_output = diff(repo_path)
        artifact = _write_artifact(
            root, f"{session_id}_repo_diff_start.patch", diff_output
        )
        baseline_event["links"].append({"kind": "artifact", "ref": str(artifact)})

    append_line(events_path, start_event)
    append_line(events_path, baseline_event)
    append_line(sessions_path, start_event)

    bitacora_path = _write_bitacora_start(
        root,
        session["day_id"],
        session_id,
        args.intent,
        args.dod,
        args.mode,
        str(repo_path),
        branch,
        start_sha,
    )

    # Generar recordatorio para Cursor en el repo activo
    reminder_path = repo_path / ".cursorrules"
    write_reminder_to_file(reminder_path)

    # Ejecutar repo-snapshot automáticamente (silencioso)
    try:
        snapshot_args = argparse.Namespace()
        snapshot_args.repo = str(repo_path)
        snapshot_args.data_root = args.data_root
        snapshot_args.scope = "structure"
        snapshot_args.actor = args.actor
        snapshot_args.user_type = args.user_type
        snapshot_args.role = args.role
        snapshot_args.client = args.client
        snapshot_args.project = args.project
        snapshot_args.area = args.area
        snapshot_args.context = args.context
        cmd_repo_snapshot(snapshot_args)
    except Exception as e:
        # No fallar si el snapshot falla, solo loguear
        print(f"Advertencia: no se pudo crear snapshot automático: {e}", file=sys.stderr)

    print(f"Sesion {session_id} iniciada. Bitacora: {bitacora_path}")
    return 0


def cmd_pre_feat(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa para este repo.", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    start_sha = current.get("repo", {}).get("start_sha")
    if not start_sha:
        start_sha = empty_tree_sha(repo_path)

    head = head_sha(repo_path)
    if head is None:
        files = changed_files_working(repo_path)
    else:
        files = changed_files(repo_path, f"{start_sha}..HEAD")
    rules = load_rules(config.rules_path(root))
    
    # Buscar error activo sin fix
    day_id_val = current["session"]["day_id"]
    active_error = find_last_unfixed_capture(events_path, session_id, day_id_val)
    
    if active_error:
        # Hay un error activo, sugerir mensaje de fix
        error_hash = active_error.get("payload", {}).get("error_hash", "")[:8]
        error_title = active_error.get("payload", {}).get("title", "error")
        message = f'🦾 fix: {error_title} [dia] [#sesion {session_id}] [#error {error_hash}]'
        error_ref = {
            "error_event_id": active_error.get("event_id"),
            "error_hash": active_error.get("payload", {}).get("error_hash"),
        }
    else:
        # Mensaje normal
        message = _suggest_commit_message(session_id, rules, files)
        error_ref = None
    
    # Usar git-commit-cursor para commits de Cursor/IA (autoría identificable)
    cli_root = Path(__file__).resolve().parents[1]
    commit_cursor_path = cli_root / "git-commit-cursor"
    if commit_cursor_path.exists():
        command = f'git-commit-cursor -m "{message}"'
    else:
        # Fallback si no está en PATH
        command = f'{commit_cursor_path} -m "{message}"'

    payload = {"command": command, "files": files}
    if error_ref:
        payload["error_ref"] = error_ref

    event = _build_event(
        "CommitSuggestionIssued",
        session={"day_id": current["session"]["day_id"], "session_id": session_id},
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=_repo_payload(repo_path, current_branch(repo_path), start_sha),
        payload=payload,
    )
    append_line(events_path, event)

    print(command)
    return 0


def cmd_end(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    sessions_path = _sessions_path(root)

    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa para este repo.", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    start_sha = current.get("repo", {}).get("start_sha")
    if not start_sha:
        start_sha = empty_tree_sha(repo_path)

    branch = current_branch(repo_path)
    end_sha = head_sha(repo_path)
    if end_sha is None:
        files = changed_files_working(repo_path)
        commits = ""
        commit_count = 0
        diff_output = diff(repo_path)
    else:
        files = changed_files(repo_path, f"{start_sha}..{end_sha}")
        commits = log_oneline(repo_path, f"{start_sha}..{end_sha}")
        commit_count = len([line for line in commits.splitlines() if line.strip()])
        diff_output = diff(repo_path, f"{start_sha}..{end_sha}")
    diff_artifact = _write_artifact(root, f"{session_id}_repo_diff_end.patch", diff_output)

    session = {
        "day_id": current["session"]["day_id"],
        "session_id": session_id,
        "result": "closed",
    }
    repo_state = _repo_payload(repo_path, branch, start_sha)
    repo_state["end_sha"] = end_sha
    repo_state["dirty"] = bool(status_porcelain(repo_path))

    diff_event = _build_event(
        "RepoDiffComputed",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=repo_state,
        payload={"files_changed": len(files), "commits": commit_count},
        links=[{"kind": "artifact", "ref": str(diff_artifact)}],
    )
    tasks = _cleanup_tasks(load_rules(config.rules_path(root)), files)
    cleanup_event = _build_event(
        "CleanupTaskGenerated",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=None,
        payload={"tasks": tasks},
    )
    end_event = _build_event(
        "SessionEnded",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=repo_state,
        payload={
            "cmd": "dia end",
            "duration_min": None,
        },
    )
    append_line(events_path, diff_event)
    append_line(events_path, cleanup_event)
    append_line(events_path, end_event)
    append_line(sessions_path, end_event)

    # Actualizar bitácora de jornada con cierre de sesión
    jornada_path = config.bitacora_dir(root) / f"{session['day_id']}.md"
    from .utils import append_to_jornada_auto_section
    
    end_info = (
        f"- {now_iso()} — SessionEnded\n"
        f"- end_sha: {end_sha or 'None'}\n"
        f"- commits: {commit_count}\n"
        f"- archivos_tocados: {len(files)}\n"
    )
    append_to_jornada_auto_section(jornada_path, end_info)
    
    # Generar archivos de cierre y limpieza (legacy, mantener por compatibilidad)
    summary = f"{commit_count} commits, {len(files)} archivos tocados."
    cierre_path = config.bitacora_dir(root) / session["day_id"] / f"CIERRE_{session_id}.md"
    limpieza_path = (
        config.bitacora_dir(root) / session["day_id"] / f"LIMPIEZA_{session_id}.md"
    )
    cierre_path.parent.mkdir(parents=True, exist_ok=True)
    limpieza_path.parent.mkdir(parents=True, exist_ok=True)
    write_text(cierre_path, cierre_template(session["day_id"], session_id, summary, [], "Revisar limpieza"))
    write_text(limpieza_path, limpieza_template(session["day_id"], session_id, tasks))
    
    # Ejecutar repo-audit automáticamente (silencioso)
    try:
        audit_args = argparse.Namespace()
        audit_args.repo = str(repo_path)
        audit_args.data_root = args.data_root
        audit_args.against = "last"
        audit_args.actor = args.actor
        audit_args.user_type = args.user_type
        audit_args.role = args.role
        audit_args.client = args.client
        audit_args.project = args.project
        audit_args.area = args.area
        audit_args.context = args.context
        cmd_repo_audit(audit_args)
    except Exception as e:
        # No fallar si el audit falla, solo loguear
        print(f"Advertencia: no se pudo ejecutar auditoría automática: {e}", file=sys.stderr)
    
    print(f"Sesion {session_id} cerrada. Bitacora jornada: {jornada_path}")
    return 0


def cmd_pause(args: argparse.Namespace) -> int:
    """Pausa la sesión activa actual."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    sessions_path = _sessions_path(root)

    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa o pausada para este repo.", file=sys.stderr)
        return 1

    # Verificar que la sesión esté activa (no paused)
    active = active_session(events_path, repo_path=str(repo_path))
    if not active:
        print("La sesión actual ya está pausada.", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    session = {
        "day_id": current["session"]["day_id"],
        "session_id": session_id,
    }

    pause_event = _build_event(
        "SessionPaused",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=None,
        payload={
            "cmd": "dia pause",
            "reason": args.reason or None,
        },
    )
    append_line(events_path, pause_event)
    append_line(sessions_path, pause_event)

    # Actualizar bitácora
    jornada_path = config.bitacora_dir(root) / f"{session['day_id']}.md"
    from .utils import append_to_jornada_auto_section
    reason_text = f" — {args.reason}" if args.reason else ""
    pause_info = f"- {now_iso()} — SessionPaused{reason_text}\n"
    append_to_jornada_auto_section(jornada_path, pause_info)

    print(f"Sesion {session_id} pausada.")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    """Reanuda una sesión pausada."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    sessions_path = _sessions_path(root)

    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa o pausada para este repo.", file=sys.stderr)
        return 1

    # Verificar que la sesión esté paused (no activa)
    active = active_session(events_path, repo_path=str(repo_path))
    if active:
        print("La sesión actual ya está activa (no está pausada).", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    session = {
        "day_id": current["session"]["day_id"],
        "session_id": session_id,
    }

    resume_event = _build_event(
        "SessionResumed",
        session=session,
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=None,
        payload={
            "cmd": "dia resume",
        },
    )
    append_line(events_path, resume_event)
    append_line(sessions_path, resume_event)

    # Actualizar bitácora
    jornada_path = config.bitacora_dir(root) / f"{session['day_id']}.md"
    from .utils import append_to_jornada_auto_section
    resume_info = f"- {now_iso()} — SessionResumed\n"
    append_to_jornada_auto_section(jornada_path, resume_info)

    print(f"Sesion {session_id} reanudada.")
    return 0


def cmd_day_status(args: argparse.Namespace) -> int:
    """Muestra el estado del día actual."""
    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    day = day_id()
    
    # Leer eventos del día
    events = list(read_json_lines(events_path))
    day_events = [e for e in events if e.get("session", {}).get("day_id") == day]
    
    # Verificar si está cerrado
    day_closed = any(e.get("type") == "DayClosed" for e in day_events)
    
    # Buscar sesiones activas/pausadas
    active_sessions = []
    paused_sessions = []
    
    sessions: dict[str, dict[str, Any]] = {}
    for event in day_events:
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
    
    for session_id, entry in sessions.items():
        if entry["ended"] is None:  # Sesión no terminada
            # Verificar si está paused
            is_paused = False
            if entry["paused"]:
                if not entry["resumed"]:
                    is_paused = True
                else:
                    paused_ts = entry["paused"].get("ts", "")
                    resumed_ts = entry["resumed"].get("ts", "")
                    if paused_ts > resumed_ts:
                        is_paused = True
            
            session_info = {
                "session_id": session_id,
                "start_ts": entry["started"].get("ts"),
                "repo": entry["started"].get("repo", {}).get("path", "N/A"),
                "intent": entry["started"].get("session", {}).get("intent", ""),
            }
            
            if is_paused:
                paused_sessions.append(session_info)
            else:
                active_sessions.append(session_info)
    
    # Mostrar estado
    print(f"Día: {day}")
    print(f"Estado: {'Cerrado' if day_closed else 'Abierto'}")
    print(f"\nSesiones activas: {len(active_sessions)}")
    for s in active_sessions:
        print(f"  - {s['session_id']}: {s['repo']} (inicio: {s['start_ts']})")
        if s['intent']:
            print(f"    Intent: {s['intent']}")
    
    print(f"\nSesiones pausadas: {len(paused_sessions)}")
    for s in paused_sessions:
        print(f"  - {s['session_id']}: {s['repo']} (inicio: {s['start_ts']})")
        if s['intent']:
            print(f"    Intent: {s['intent']}")
    
    if not active_sessions and not paused_sessions:
        print("\nNo hay sesiones activas o pausadas.")
    
    return 0


def cmd_day_close(args: argparse.Namespace) -> int:
    """Cierra la jornada (ritual humano). Valida que no haya sesiones activas/pausadas y genera summary nightly."""
    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    day = day_id()
    
    # Verificar si ya está cerrado
    events = list(read_json_lines(events_path))
    day_events = [e for e in events if e.get("session", {}).get("day_id") == day]
    already_closed = any(e.get("type") == "DayClosed" for e in day_events)
    
    if already_closed:
        print(f"Jornada {day} ya está cerrada.", file=sys.stderr)
        return 1
    
    # Validar que no haya sesiones activas o pausadas (incluyendo huérfanas)
    events = list(read_json_lines(events_path))
    ended_sessions: set[str] = set()
    orphan_sessions: list[dict[str, Any]] = []
    
    # Identificar sesiones cerradas
    for event in events:
        if event.get("type") in ("SessionEnded", "SessionForceClosed"):
            session_id = event.get("session", {}).get("session_id")
            if session_id:
                ended_sessions.add(session_id)
    
    # Buscar sesiones huérfanas (started sin ended)
    for event in events:
        event_type = event.get("type")
        if event_type in ("SessionStarted", "SessionStartedAfterDayClosed"):
            session_id = event.get("session", {}).get("session_id")
            if session_id and session_id not in ended_sessions:
                orphan_sessions.append({
                    "session_id": session_id,
                    "day_id": event.get("session", {}).get("day_id"),
                    "start_ts": event.get("ts"),
                    "repo": event.get("repo", {}).get("path", "N/A"),
                })
    
    if orphan_sessions:
        print(f"Error: No puedo cerrar el día: hay {len(orphan_sessions)} sesión(es) sin cerrar:", file=sys.stderr)
        for sess in orphan_sessions:
            print(f"  - {sess['session_id']} (día {sess['day_id']}, repo: {sess['repo']})", file=sys.stderr)
        print("\nSugerencias:", file=sys.stderr)
        print("  - Para sesión del día actual: 'dia session end'", file=sys.stderr)
        print("  - Para sesión huérfana: 'dia session close --id <session_id> --reason \"...\"'", file=sys.stderr)
        return 1
    
    # Generar summary nightly antes de cerrar
    if not getattr(args, 'skip_summary', False):
        print(f"Generando summary nightly para {day}...")
        summary_args = argparse.Namespace()
        summary_args.data_root = args.data_root
        summary_args.day_id = day
        summary_args.mode = "nightly"
        summary_args.actor = args.actor
        summary_args.user_type = args.user_type
        summary_args.role = args.role
        summary_args.client = args.client
        summary_args.project = args.project
        summary_args.area = args.area
        summary_args.context = args.context
        summary_args.force = True  # Permitir nightly aunque el día no esté cerrado aún
        
        result = cmd_summary_nightly(summary_args)
        if result != 0:
            print("Advertencia: No se pudo generar summary nightly, pero continuando con cierre del día.", file=sys.stderr)
    
    # Registrar evento DayClosed
    close_event = _build_event(
        "DayClosed",
        session={"day_id": day, "session_id": None},
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=None,
        payload={"closed_at": now_iso()},
    )
    
    append_line(events_path, close_event)
    
    # Opcionalmente agregar marca a bitácora
    jornada_path = config.bitacora_dir(root) / f"{day}.md"
    if jornada_path.exists():
        from .utils import append_to_jornada_auto_section
        close_mark = f"\n- {now_iso()} — DayClosed (cierre humano)\n"
        append_to_jornada_auto_section(jornada_path, close_mark)
    
    print(f"Jornada {day} cerrada. Evento DayClosed registrado.")
    return 0


def cmd_close_day(args: argparse.Namespace) -> int:
    """Alias legacy para cmd_day_close."""
    return cmd_day_close(args)


def cmd_summary_rolling(args: argparse.Namespace) -> int:
    """Genera resumen rolling (estado liviano incremental para sesión activa)."""
    from .summaries import extract_objective, generate_summary
    
    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    
    # Determinar día
    day_id_val = args.day_id if args.day_id else day_id()
    
    # Verificar que haya sesión activa
    active = active_session(events_path)
    if not active:
        print("Error: No hay sesión activa. Rolling summary requiere sesión activa.", file=sys.stderr)
        return 1
    
    # Leer eventos del día
    events = list(read_json_lines(events_path))
    day_events = [e for e in events if e.get("session", {}).get("day_id") == day_id_val]
    
    if not day_events:
        print(f"No hay eventos registrados para {day_id_val}.", file=sys.stderr)
        return 1
    
    # Leer bitácora para extraer objetivo
    jornada_path = config.bitacora_dir(root) / f"{day_id_val}.md"
    objective = extract_objective(jornada_path)
    
    # Ruta del índice de resúmenes (summaries.ndjson)
    summaries_path = config.index_dir(root) / "summaries.ndjson"
    
    # Generar resumen
    summary_data = generate_summary(
        root=root,
        day_id_val=day_id_val,
        mode="rolling",
        events=day_events,
        objective=objective,
        summaries_path=summaries_path,
    )
    
    # Construir evento completo
    event = _build_event(
        summary_data["event_type"],
        session=summary_data["session"],
        actor=summary_data["actor"],
        project=summary_data["project"],
        repo=summary_data["repo"],
        payload=summary_data["payload"],
        links=summary_data["links"],
    )
    
    # Guardar en índice y events
    append_line(summaries_path, event)
    append_line(events_path, event)
    
    print(f"Resumen rolling generado para {day_id_val}")
    print(f"Assessment: {summary_data['payload']['assessment']}")
    print(f"Próximo paso: {summary_data['payload']['next_step']}")
    if summary_data['payload'].get('blocker'):
        print(f"Blocker: {summary_data['payload']['blocker']}")
    if summary_data['payload'].get('links'):
        print(f"Artefacto: {summary_data['payload']['links'][0]['ref']}")
    
    return 0


def cmd_summary_nightly(args: argparse.Namespace) -> int:
    """Genera resumen nightly (informe largo consolidado del día)."""
    from .summaries import extract_objective, generate_summary
    
    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)
    
    # Determinar día
    day_id_val = args.day_id if args.day_id else day_id()
    
    # Leer eventos del día
    events = list(read_json_lines(events_path))
    day_events = [e for e in events if e.get("session", {}).get("day_id") == day_id_val]
    
    if not day_events:
        print(f"No hay eventos registrados para {day_id_val}.", file=sys.stderr)
        return 1
    
    # Verificar si el día está cerrado (a menos que se use --force)
    day_closed = any(e.get("type") == "DayClosed" for e in day_events)
    if not day_closed and not getattr(args, 'force', False):
        print(f"Advertencia: Día {day_id_val} no está cerrado.", file=sys.stderr)
        print("Sugerencia: Ejecuta 'dia day close' primero, o usa --force para forzar.", file=sys.stderr)
        confirm = input("¿Continuar de todas formas? (escriba 'si' para confirmar): ").strip().lower()
        if confirm not in {"si", "s", "yes", "y"}:
            return 1
    
    # Leer bitácora para extraer objetivo
    jornada_path = config.bitacora_dir(root) / f"{day_id_val}.md"
    objective = extract_objective(jornada_path)
    
    # Ruta del índice de resúmenes (summaries.ndjson)
    summaries_path = config.index_dir(root) / "summaries.ndjson"
    
    # Generar resumen
    summary_data = generate_summary(
        root=root,
        day_id_val=day_id_val,
        mode="nightly",
        events=day_events,
        objective=objective,
        summaries_path=summaries_path,
    )
    
    # Construir evento completo
    event = _build_event(
        summary_data["event_type"],
        session=summary_data["session"],
        actor=summary_data["actor"],
        project=summary_data["project"],
        repo=summary_data["repo"],
        payload=summary_data["payload"],
        links=summary_data["links"],
    )
    
    # Guardar en índice y events
    append_line(summaries_path, event)
    append_line(events_path, event)
    
    print(f"Resumen nightly generado para {day_id_val}")
    print(f"Assessment: {summary_data['payload']['assessment']}")
    print(f"Próximo paso: {summary_data['payload']['next_step']}")
    if summary_data['payload'].get('blocker'):
        print(f"Blocker: {summary_data['payload']['blocker']}")
    if summary_data['payload'].get('links'):
        print(f"Artefacto: {summary_data['payload']['links'][0]['ref']}")
    
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    """Alias legacy para cmd_summary_rolling o cmd_summary_nightly según --mode."""
    if args.mode == "rolling":
        return cmd_summary_rolling(args)
    elif args.mode == "nightly":
        return cmd_summary_nightly(args)
    else:
        print(f"Modo inválido: {args.mode}", file=sys.stderr)
        return 1


def cmd_cap(args: argparse.Namespace) -> int:
    """Captura texto (logs/errores) y lo guarda como artifact + evento NDJSON."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    # Verificar sesión activa
    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa para este repo.", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    day_id_val = current["session"]["day_id"]

    # Leer contenido desde stdin
    if args.stdin or not sys.stdin.isatty():
        content = sys.stdin.read()
    else:
        print("Pegar contenido (Ctrl-D para finalizar):", file=sys.stderr)
        content = sys.stdin.read()

    if not content.strip():
        print("Contenido vacio.", file=sys.stderr)
        return 1

    # Generar título automáticamente si se usa --auto o si no se proporciona --title
    title = args.title
    if args.auto or (not title and args.kind == "error"):
        # Verificar si hay LLM disponible
        has_llm = os.getenv("OPENAI_API_KEY") is not None
        if has_llm:
            print("Generando título con LLM...", file=sys.stderr)
        generated_title = analyze_error_with_llm(content, args.kind)
        if generated_title:
            title = generated_title
            if has_llm:
                print(f"Título generado: {title}", file=sys.stderr)
            else:
                print(f"Título generado: {title}", file=sys.stderr)
        else:
            # Fallback: usar análisis simple
            title = _analyze_error_simple(content)
            print(f"Título generado: {title}", file=sys.stderr)
    
    if not title:
        print("Error: se requiere --title o usar --auto", file=sys.stderr)
        return 1

    # Calcular hash
    error_hash = compute_content_hash(content)

    # Verificar si ya existe este error y buscar errores similares
    events = list(read_json_lines(events_path))
    existing_capture = None
    similar_errors = []
    
    for event in events:
        if event.get("type") == "CaptureCreated":
            event_hash = event.get("payload", {}).get("error_hash")
            if event_hash == error_hash:
                existing_capture = event
            elif event_hash:
                # Buscar errores similares (mismo título o palabras clave)
                event_title = event.get("payload", {}).get("title", "").lower()
                current_title_lower = (title or "").lower()
                # Si comparten palabras clave importantes
                if event_title and current_title_lower:
                    event_words = set(event_title.split())
                    current_words = set(current_title_lower.split())
                    common_words = event_words.intersection(current_words)
                    # Si comparten al menos 2 palabras significativas
                    if len(common_words) >= 2:
                        similar_errors.append(event)

    # Obtener estado del repo
    branch = current_branch(repo_path)
    head = head_sha(repo_path)

    # Generar capture_id
    capture_id = f"cap_{uuid.uuid4().hex[:12]}"

    # Crear estructura de directorios
    capture_dir = captures_dir(root) / day_id_val / session_id
    capture_dir.mkdir(parents=True, exist_ok=True)

    # Guardar artifact
    artifact_path = capture_dir / f"{capture_id}.txt"
    write_text(artifact_path, content)

    # Guardar meta.json
    meta = {
        "capture_id": capture_id,
        "kind": args.kind,
        "title": title,
        "content_hash": error_hash,
        "repo": {
            "path": str(repo_path),
            "branch": branch,
            "head_sha": head,
        },
        "session": {
            "day_id": day_id_val,
            "session_id": session_id,
        },
        "timestamp": now_iso(),
    }
    meta_path = capture_dir / f"{capture_id}.meta.json"
    write_text(meta_path, json.dumps(meta, indent=2))

    # Path relativo para el artifact
    artifact_ref = f"artifacts/captures/{day_id_val}/{session_id}/{capture_id}.txt"

    # Construir evento
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    }
    actor = _actor_from_args(args)
    project = _project_from_args(args)
    repo_state = _repo_payload(repo_path, branch, head)

    if existing_capture:
        # Error repetido
        event = _build_event(
            "CaptureReoccurred",
            session=session,
            actor=actor,
            project=project,
            repo=repo_state,
            payload={
                "error_hash": error_hash,
                "original_event_id": existing_capture.get("event_id"),
                "artifact_ref": artifact_ref,
                "title": title,
            },
            links=[{"kind": "artifact", "ref": artifact_ref}],
        )
    else:
        # Error nuevo
        event = _build_event(
            "CaptureCreated",
            session=session,
            actor=actor,
            project=project,
            repo=repo_state,
            payload={
                "kind": args.kind,
                "title": title,
                "error_hash": error_hash,
                "artifact_ref": artifact_ref,
            },
            links=[{"kind": "artifact", "ref": artifact_ref}],
        )

    append_line(events_path, event)

    # Mostrar resultado
    if existing_capture:
        print(f"⚠️  Error repetido detectado (hash: {error_hash[:8]}...)")
        print(f"   Original: {existing_capture.get('ts', 'N/A')} - {existing_capture.get('payload', {}).get('title', 'Sin título')}")
        print(f"   Sesión original: {existing_capture.get('session', {}).get('session_id', 'N/A')}")
        
        # Verificar si el error original tiene fix
        original_event_id = existing_capture.get("event_id")
        has_fix = any(
            e.get("type") == "FixLinked" 
            and e.get("payload", {}).get("error_event_id") == original_event_id
            for e in events
        )
        
        if has_fix:
            print(f"   ℹ️  Este error ya fue resuelto anteriormente")
        else:
            print(f"   ⚠️  Este error aún no tiene fix asociado")
            print(f"   💡 Sugerencia: Revisa el fix anterior o aplica uno nuevo con 'dia fix'")
    else:
        print(f"✅ Captura creada: {capture_id}")
        print(f"   Artifact: {artifact_path}")
        print(f"   Meta: {meta_path}")
        
        # Mostrar errores similares si existen
        if similar_errors:
            print(f"\n   📋 Errores similares encontrados ({len(similar_errors)}):")
            for similar in similar_errors[:3]:  # Mostrar máximo 3
                similar_title = similar.get("payload", {}).get("title", "Sin título")
                similar_session = similar.get("session", {}).get("session_id", "N/A")
                similar_ts = similar.get("ts", "N/A")
                print(f"      - {similar_title} (Sesión {similar_session}, {similar_ts[:10]})")
        
        # Sugerir acciones siguientes según el flujo
        print(f"\n   💡 Próximos pasos:")
        print(f"      1. Revisar artifact: {artifact_path}")
        print(f"      2. Analizar y aplicar fix")
        print(f"      3. Linkear fix: dia fix --title \"descripción del fix\" --data-root {root} --area {args.area}")
        print(f"      4. Commit: dia pre-feat --data-root {root} --area {args.area}")

    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Linkea un fix a un error capturado."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    # Verificar sesión activa
    current = current_session(events_path, repo_path=str(repo_path))
    if not current:
        print("No hay sesion activa para este repo.", file=sys.stderr)
        return 1

    session_id = current["session"]["session_id"]
    day_id_val = current["session"]["day_id"]

    # Buscar último error sin fix
    if args.from_capture:
        # Buscar por capture_id específico
        events = list(read_json_lines(events_path))
        target_capture = None
        for event in events:
            if event.get("type") == "CaptureCreated":
                artifact_ref = event.get("payload", {}).get("artifact_ref", "")
                if args.from_capture in artifact_ref:
                    target_capture = event
                    break
        if not target_capture:
            print(f"Capture {args.from_capture} no encontrado.", file=sys.stderr)
            return 1
    else:
        # Buscar último sin fix
        target_capture = find_last_unfixed_capture(events_path, session_id, day_id_val)
        if not target_capture:
            print("No hay errores sin fix en esta sesion.", file=sys.stderr)
            return 1

    # Obtener estado del repo
    branch = current_branch(repo_path)
    fix_sha = head_sha(repo_path)  # Puede ser None si working tree

    # Construir evento FixLinked
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    }
    actor = _actor_from_args(args)
    project = _project_from_args(args)
    repo_state = _repo_payload(repo_path, branch, None)
    repo_state["end_sha"] = fix_sha

    error_hash = target_capture.get("payload", {}).get("error_hash")
    error_event_id = target_capture.get("event_id")

    # Generar fix_id único para referenciar este fix posteriormente
    fix_id = f"fix_{uuid.uuid4().hex[:12]}"

    fix_event = _build_event(
        "FixLinked",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "fix_id": fix_id,
            "error_event_id": error_event_id,
            "error_hash": error_hash,
            "fix_sha": fix_sha,
            "title": args.title,
        },
    )

    append_line(events_path, fix_event)

    print(f"Fix linkeado a error: {error_hash[:8]}...")
    print(f"Fix ID: {fix_id}")
    print(f"Error event_id: {error_event_id}")
    if fix_sha:
        print(f"Fix commit: {fix_sha}")
    else:
        print("Fix en working tree (aun sin commit)")
        print("Ejecuta 'dia pre-feat' para sugerir commit")
        print(f"Luego usa 'dia fix-commit --fix {fix_id} --last' para linkear el commit")

    return 0


def cmd_fix_commit(args: argparse.Namespace) -> int:
    """Linkea un fix a un commit específico."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    # Determinar commit SHA
    if args.last:
        commit_sha = head_sha(repo_path)
        if not commit_sha:
            print("No hay commit HEAD en este repo.", file=sys.stderr)
            return 1
    elif args.commit:
        commit_sha = args.commit
        # Validar que el commit existe
        try:
            run_git(repo_path, ["rev-parse", "--verify", commit_sha])
        except RuntimeError:
            print(f"Commit {commit_sha} no encontrado en el repo.", file=sys.stderr)
            return 1
    else:
        print("Error: se requiere --commit <sha> o --last", file=sys.stderr)
        return 1

    # Buscar el FixLinked por fix_id
    events = list(read_json_lines(events_path))
    fix_linked = None
    for event in events:
        if event.get("type") == "FixLinked":
            payload = event.get("payload", {})
            if payload.get("fix_id") == args.fix_id:
                fix_linked = event
                break

    if not fix_linked:
        print(f"Fix {args.fix_id} no encontrado.", file=sys.stderr)
        return 1

    # Obtener sesión: usar sesión activa si existe, sino usar la del FixLinked
    current = current_session(events_path, repo_path=str(repo_path))
    if current:
        session_id = current["session"]["session_id"]
        day_id_val = current["session"]["day_id"]
    else:
        # Usar sesión del FixLinked
        fix_session = fix_linked.get("session", {})
        session_id = fix_session.get("session_id")
        day_id_val = fix_session.get("day_id")
        if not session_id or not day_id_val:
            print("No se pudo determinar sesión para el fix.", file=sys.stderr)
            return 1

    # Verificar que no esté ya linkeado
    fix_event_id = fix_linked.get("event_id")
    already_committed = any(
        e.get("type") == "FixCommitted"
        and e.get("payload", {}).get("fix_event_id") == fix_event_id
        for e in events
    )

    if already_committed:
        existing = next(
            e for e in events
            if e.get("type") == "FixCommitted"
            and e.get("payload", {}).get("fix_event_id") == fix_event_id
        )
        existing_sha = existing.get("payload", {}).get("commit_sha")
        print(f"Fix {args.fix_id} ya está linkeado al commit {existing_sha}")
        return 0

    # Construir evento FixCommitted
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    }
    actor = _actor_from_args(args)
    project = _project_from_args(args)
    repo_state = _repo_payload(repo_path, current_branch(repo_path), None)

    fix_committed_event = _build_event(
        "FixCommitted",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "fix_event_id": fix_event_id,
            "fix_id": args.fix_id,
            "commit_sha": commit_sha,
            "error_event_id": fix_linked.get("payload", {}).get("error_event_id"),
        },
    )

    append_line(events_path, fix_committed_event)

    print(f"Fix {args.fix_id} linkeado al commit {commit_sha}")
    print(f"Error event_id: {fix_linked.get('payload', {}).get('error_event_id')}")
    print(f"Commit SHA: {commit_sha}")

    return 0


def cmd_repo_snapshot(args: argparse.Namespace) -> int:
    """Captura snapshot liviano de estructura del repo."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    if not is_git_repo(repo_path):
        print("Repo invalido o no es git.", file=sys.stderr)
        return 1

    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    # Verificar sesión activa (opcional, pero preferible)
    current = current_session(events_path, repo_path=str(repo_path))
    session_id = current["session"]["session_id"] if current else None
    day_id_val = current["session"]["day_id"] if current else day_id()

    # Capturar snapshot liviano
    head = head_sha(repo_path)
    tracked_paths = []
    if head:
        ls_tree_output = ls_tree(repo_path, head)
        if ls_tree_output:
            tracked_paths = [line.strip() for line in ls_tree_output.splitlines() if line.strip()]
    
    status_output = status_porcelain(repo_path)
    status_lines = [line.strip() for line in status_output.splitlines() if line.strip()] if status_output else []

    # Construir snapshot
    snapshot_data = {
        "timestamp": now_iso(),
        "repo_path": str(repo_path),
        "branch": current_branch(repo_path),
        "head_sha": head,
        "tracked_files": tracked_paths,
        "status_porcelain": status_lines,
        "scope": args.scope,
    }

    # Guardar artifact
    from datetime import datetime
    from .utils import TZ_BUENOS_AIRES
    timestamp_str = datetime.now(TZ_BUENOS_AIRES).strftime("%Y%m%d_%H%M%S")
    snapshot_dir = config.artifacts_dir(root) / "snapshots"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    snapshot_file = snapshot_dir / f"repo_structure_{timestamp_str}.json"
    write_text(snapshot_file, json.dumps(snapshot_data, indent=2))

    # Crear evento
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    } if session_id else {"day_id": day_id_val, "session_id": None}
    
    actor = _actor_from_args(args)
    project = _project_from_args(args)
    repo_state = _repo_payload(repo_path, current_branch(repo_path), head)

    snapshot_event = _build_event(
        "RepoSnapshotCreated",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "scope": args.scope,
            "tracked_files_count": len(tracked_paths),
            "status_lines_count": len(status_lines),
        },
        links=[{"kind": "artifact", "ref": str(snapshot_file.relative_to(root))}],
    )

    append_line(events_path, snapshot_event)

    print(f"Snapshot creado: {snapshot_file.name}")
    print(f"  Archivos trackeados: {len(tracked_paths)}")
    print(f"  Líneas de status: {len(status_lines)}")
    print(f"  Artifact: {snapshot_file}")

    return 0


def cmd_repo_audit(args: argparse.Namespace) -> int:
    """Audita estructura del repo contra snapshot."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    if not is_git_repo(repo_path):
        print("Repo invalido o no es git.", file=sys.stderr)
        return 1

    root = config.data_root(args.data_root, repo_path=repo_path)
    config.ensure_data_dirs(root)
    events_path = _events_path(root)

    # Verificar sesión activa
    current = current_session(events_path, repo_path=str(repo_path))
    session_id = current["session"]["session_id"] if current else None
    day_id_val = current["session"]["day_id"] if current else day_id()

    # Cargar snapshot
    snapshot_dir = config.artifacts_dir(root) / "snapshots"
    snapshot_file = None
    
    if args.against == "last":
        # Buscar último snapshot
        snapshots = sorted(snapshot_dir.glob("repo_structure_*.json"), reverse=True)
        if not snapshots:
            print("No hay snapshots disponibles. Ejecuta 'dia repo-snapshot' primero.", file=sys.stderr)
            return 1
        snapshot_file = snapshots[0]
    else:
        # Buscar por ID/timestamp
        snapshot_file = snapshot_dir / f"repo_structure_{args.against}.json"
        if not snapshot_file.exists():
            # Intentar sin extensión
            snapshot_file = snapshot_dir / f"repo_structure_{args.against}"
            if not snapshot_file.exists():
                print(f"Snapshot {args.against} no encontrado.", file=sys.stderr)
                return 1

    # Leer snapshot
    snapshot_data = json.loads(read_text(snapshot_file))
    snapshot_tracked = set(snapshot_data.get("tracked_files", []))
    snapshot_status = set(snapshot_data.get("status_porcelain", []))

    # Capturar estado actual
    head = head_sha(repo_path)
    current_tracked = set()
    if head:
        ls_tree_output = ls_tree(repo_path, head)
        if ls_tree_output:
            current_tracked = set(line.strip() for line in ls_tree_output.splitlines() if line.strip())
    
    status_output = status_porcelain(repo_path)
    current_status = set(line.strip() for line in status_output.splitlines() if line.strip()) if status_output else set()

    # Detectar cambios
    new_files = current_tracked - snapshot_tracked
    removed_files = snapshot_tracked - current_tracked
    modified_files = set()
    for status_line in current_status:
        # git status --porcelain: XY path
        # X = staged, Y = working tree
        # M = modified, A = added, D = deleted, etc.
        if len(status_line) >= 3:
            status_code = status_line[:2]
            file_path = status_line[3:].strip()
            if "M" in status_code or "A" in status_code:
                modified_files.add(file_path)

    # Cargar reglas
    structure_rules = load_repo_structure_rules(root)
    rules = structure_rules.get("rules", [])

    # Aplicar reglas y generar eventos
    violations = []
    session = {
        "day_id": day_id_val,
        "session_id": session_id,
    } if session_id else {"day_id": day_id_val, "session_id": None}
    
    actor = _actor_from_args(args)
    project = _project_from_args(args)
    repo_state = _repo_payload(repo_path, current_branch(repo_path), head)

    # Regla 1: En raíz solo README.md como .md
    root_md_rule = next((r for r in rules if r.get("id") == "root_only_readme"), None)
    if root_md_rule:
        root_md_files = [
            f for f in current_tracked 
            if f.endswith(".md") 
            and "/" not in f 
            and f != "README.md"
            and not f.startswith("node_modules/")  # Excluir node_modules (aunque no debería estar en raíz)
        ]
        if root_md_files:
            for md_file in root_md_files:
                violation_event = _build_event(
                    "UnexpectedFileInRootDetected",
                    session=session,
                    actor=actor,
                    project=project,
                    repo=repo_state,
                    payload={
                        "file": md_file,
                        "rule_id": root_md_rule.get("id"),
                        "suggestion": "Mover a docs_temp/ y clasificar",
                    },
                )
                append_line(events_path, violation_event)
                violations.append(violation_event)

    # Regla 2: .md fuera de docs/ es sospechoso
    # Permite README.md en raíz del proyecto y en raíz de módulos/herramientas (cli/, server/, ui/, etc.)
    suspicious_md_rule = next((r for r in rules if r.get("id") == "suspicious_md_outside_docs"), None)
    if suspicious_md_rule:
        suspicious_files = []
        for f in current_tracked:
            if not f.endswith(".md"):
                continue
            if f.startswith("docs/"):
                continue
            if f == "README.md":  # Raíz del proyecto
                continue
            if f.startswith("node_modules/") or "node_modules/" in f:
                continue
            # Permitir README.md en raíz de módulos/herramientas (primer nivel)
            # Ej: cli/README.md, server/README.md, ui/README.md
            if "/" in f:
                parts = f.split("/")
                if len(parts) == 2 and parts[1] == "README.md":
                    # Es un README.md en un subdirectorio de primer nivel (módulo/herramienta)
                    continue
            # Cualquier otro .md fuera de docs/ es sospechoso
            suspicious_files.append(f)
        if suspicious_files:
            for md_file in suspicious_files:
                violation_event = _build_event(
                    "SuspiciousFileDetected",
                    session=session,
                    actor=actor,
                    project=project,
                    repo=repo_state,
                    payload={
                        "file": md_file,
                        "rule_id": suspicious_md_rule.get("id"),
                        "suggestion": "Revisar y proponer mover/copy a docs_temp/",
                    },
                )
                append_line(events_path, violation_event)
                violations.append(violation_event)

    # Regla 3: Cambios en docs/ → alerta
    docs_touched_rule = next((r for r in rules if r.get("id") == "docs_touched_alert"), None)
    if docs_touched_rule:
        docs_modified = [f for f in modified_files if f.startswith("docs/")]
        if docs_modified:
            violation_event = _build_event(
                "DocsTouched",
                session=session,
                actor=actor,
                project=project,
                repo=repo_state,
                payload={
                    "files": docs_modified,
                    "rule_id": docs_touched_rule.get("id"),
                    "severity": "info",
                    "suggestion": "Revisar cambios en Zona Indeleble",
                },
            )
            append_line(events_path, violation_event)
            violations.append(violation_event)

    # Crear evento de resumen
    audit_event = _build_event(
        "RepoAuditCompleted",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "snapshot_file": str(snapshot_file.relative_to(root)),
            "violations_count": len(violations),
            "new_files_count": len(new_files),
            "removed_files_count": len(removed_files),
            "modified_files_count": len(modified_files),
        },
    )
    append_line(events_path, audit_event)

    # Mostrar resultados
    print(f"Auditoría completada contra snapshot: {snapshot_file.name}")
    print(f"  Violaciones detectadas: {len(violations)}")
    print(f"  Archivos nuevos: {len(new_files)}")
    print(f"  Archivos eliminados: {len(removed_files)}")
    print(f"  Archivos modificados: {len(modified_files)}")
    
    if violations:
        print("\n  Violaciones:")
        for v in violations:
            payload = v.get("payload", {})
            print(f"    - {v.get('type')}: {payload.get('file', payload.get('files', 'N/A'))}")

    return 0


def cmd_update(args: argparse.Namespace) -> int:
    cli_root = Path(__file__).resolve().parents[1]
    print("Reinstalando CLI en modo editable...")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", "."],
        cwd=str(cli_root),
        check=False,
    )
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dia", description="CLI /dia v0.1")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--data-root", help="Ruta base de data/", default=None)
    common.add_argument("--actor", default="u_local")
    common.add_argument("--user-type", default="human")
    common.add_argument("--role", default="director")
    common.add_argument("--client", default="cli")
    common.add_argument("--project", required=False)
    common.add_argument("--area", default="it")
    common.add_argument("--context", default="")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Namespace: session
    session_parser = subparsers.add_parser(
        "session", help="Gestión de sesiones", parents=[common]
    )
    session_subparsers = session_parser.add_subparsers(dest="session_command", required=True)
    
    session_start_parser = session_subparsers.add_parser(
        "start", help="Inicia sesión (crea day_id si no existe)", parents=[common]
    )
    session_start_parser.add_argument("--repo", required=False)
    session_start_parser.add_argument("--intent", required=False)
    session_start_parser.add_argument("--dod", required=False)
    session_start_parser.add_argument("--mode", default=None)
    session_start_parser.set_defaults(func=cmd_session_start)
    
    session_end_parser = session_subparsers.add_parser(
        "end", help="Cierra sesión activa (NO genera nightly)", parents=[common]
    )
    session_end_parser.add_argument("--repo", required=False)
    session_end_parser.set_defaults(func=cmd_session_end)
    
    session_pause_parser = session_subparsers.add_parser(
        "pause", help="Pausa sesión activa", parents=[common]
    )
    session_pause_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    session_pause_parser.add_argument("--reason", required=False, help="Razón de la pausa (opcional)")
    session_pause_parser.set_defaults(func=cmd_session_pause)
    
    session_resume_parser = session_subparsers.add_parser(
        "resume", help="Reanuda sesión pausada", parents=[common]
    )
    session_resume_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    session_resume_parser.set_defaults(func=cmd_session_resume)
    
    session_close_parser = session_subparsers.add_parser(
        "close", help="Cierra sesión por ID (reparación manual de sesiones huérfanas)", parents=[common]
    )
    session_close_parser.add_argument("--id", dest="session_id", required=True, help="ID de sesión (ej: S03)")
    session_close_parser.add_argument("--reason", required=False, help="Razón del cierre forzado")
    session_close_parser.set_defaults(func=cmd_session_close)

    # Namespace: day
    day_parser = subparsers.add_parser(
        "day", help="Gestión de días/jornadas", parents=[common]
    )
    day_subparsers = day_parser.add_subparsers(dest="day_command", required=True)
    
    day_status_parser = day_subparsers.add_parser(
        "status", help="Muestra estado del día actual", parents=[common]
    )
    day_status_parser.set_defaults(func=cmd_day_status)
    
    day_close_parser = day_subparsers.add_parser(
        "close", help="Cierra jornada (valida sesiones activas y genera nightly)", parents=[common]
    )
    day_close_parser.add_argument(
        "--skip-summary", action="store_true", help="Omitir generación automática de summary nightly"
    )
    day_close_parser.set_defaults(func=cmd_day_close)

    # Namespace: summary
    summary_parser = subparsers.add_parser(
        "summary", help="Generación de resúmenes", parents=[common]
    )
    summary_subparsers = summary_parser.add_subparsers(dest="summary_command", required=True)
    
    summary_rolling_parser = summary_subparsers.add_parser(
        "rolling", help="Resumen rolling (estado liviano incremental para sesión activa)", parents=[common]
    )
    summary_rolling_parser.add_argument(
        "--day-id", help="Día específico (default: día actual)"
    )
    summary_rolling_parser.set_defaults(func=cmd_summary_rolling)
    
    summary_nightly_parser = summary_subparsers.add_parser(
        "nightly", help="Resumen nightly (informe largo consolidado del día)", parents=[common]
    )
    summary_nightly_parser.add_argument(
        "--day-id", help="Día específico (default: día actual)"
    )
    summary_nightly_parser.add_argument(
        "--force", action="store_true", help="Forzar generación aunque el día no esté cerrado"
    )
    summary_nightly_parser.set_defaults(func=cmd_summary_nightly)

    # Aliases legacy (mantener compatibilidad)
    start_parser = subparsers.add_parser(
        "start", help="[LEGACY] Alias de 'dia session start'", parents=[common]
    )
    start_parser.add_argument("--repo", required=False)
    start_parser.add_argument("--intent", required=False)
    start_parser.add_argument("--dod", required=False)
    start_parser.add_argument("--mode", default=None)
    start_parser.set_defaults(func=cmd_start)

    end_parser = subparsers.add_parser(
        "end", help="[LEGACY] Alias de 'dia session end'", parents=[common]
    )
    end_parser.add_argument("--repo", required=False)
    end_parser.set_defaults(func=cmd_end)

    pause_parser = subparsers.add_parser(
        "pause", help="[LEGACY] Alias de 'dia session pause'", parents=[common]
    )
    pause_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    pause_parser.add_argument("--reason", required=False, help="Razón de la pausa (opcional)")
    pause_parser.set_defaults(func=cmd_pause)

    resume_parser = subparsers.add_parser(
        "resume", help="[LEGACY] Alias de 'dia session resume'", parents=[common]
    )
    resume_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    resume_parser.set_defaults(func=cmd_resume)

    close_day_parser = subparsers.add_parser(
        "close-day", help="[LEGACY] Alias de 'dia day close'", parents=[common]
    )
    close_day_parser.add_argument(
        "--skip-summary", action="store_true", help="Omitir generación automática de summary nightly"
    )
    close_day_parser.set_defaults(func=cmd_close_day)

    summarize_parser = subparsers.add_parser(
        "summarize", help="[LEGACY] Genera resumen regenerable (usar 'dia summary rolling' o 'dia summary nightly')", parents=[common]
    )
    summarize_parser.add_argument(
        "--scope", choices=["day"], default="day", help="Alcance del resumen (v0: solo day)"
    )
    summarize_parser.add_argument(
        "--mode", choices=["rolling", "nightly"], required=True, help="Modo: rolling (durante día) o nightly (final del día)"
    )
    summarize_parser.add_argument(
        "--day-id", help="Día específico (default: día actual)"
    )
    summarize_parser.set_defaults(func=cmd_summarize)

    pre_feat_parser = subparsers.add_parser(
        "pre-feat", help="Checkpoint pre-feat", parents=[common]
    )
    pre_feat_parser.add_argument("--repo", required=False)
    pre_feat_parser.set_defaults(func=cmd_pre_feat)

    repo_snapshot_parser = subparsers.add_parser(
        "repo-snapshot", help="Captura snapshot de estructura del repo", parents=[common]
    )
    repo_snapshot_parser.add_argument(
        "--scope", choices=["structure"], default="structure", help="Alcance del snapshot"
    )
    repo_snapshot_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    repo_snapshot_parser.set_defaults(func=cmd_repo_snapshot)

    repo_audit_parser = subparsers.add_parser(
        "repo-audit", help="Audita estructura del repo contra snapshot", parents=[common]
    )
    repo_audit_parser.add_argument(
        "--against", default="last", help="Snapshot ID o 'last' para el último (default: last)"
    )
    repo_audit_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    repo_audit_parser.set_defaults(func=cmd_repo_audit)

    cap_parser = subparsers.add_parser(
        "cap", help="Captura error/log desde stdin", parents=[common]
    )
    cap_parser.add_argument("--kind", required=True, choices=["error", "log"], help="Tipo de captura")
    cap_parser.add_argument("--title", required=False, help="Descripcion breve (opcional si se usa --auto)")
    cap_parser.add_argument("--auto", action="store_true", help="Generar título automáticamente con LLM")
    cap_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    cap_parser.add_argument("--stdin", action="store_true", help="Leer desde stdin (default: auto-detect)")
    cap_parser.set_defaults(func=cmd_cap)
    
    # Alias corto "E" para capturar errores con auto-título
    e_parser = subparsers.add_parser(
        "E", help="Captura error con título automático (alias de 'cap --kind error --auto')", parents=[common]
    )
    e_parser.add_argument(
        "error_message", 
        nargs="?", 
        help="Mensaje de error (opcional). Para texto largo o con caracteres especiales (como &, |), usa stdin: 'dia E < archivo.txt' o heredoc"
    )
    e_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    e_parser.add_argument("--stdin", action="store_true", help="Leer desde stdin (default: auto-detect)")
    
    def cmd_e(args):
        """Wrapper para cmd_cap con --kind error --auto"""
        # Si se proporciona mensaje como argumento, inyectarlo en stdin
        if hasattr(args, 'error_message') and args.error_message:
            import io
            import sys
            # Guardar stdin original si es necesario
            original_stdin = sys.stdin
            try:
                # Crear un StringIO con el mensaje
                sys.stdin = io.StringIO(args.error_message)
                args.stdin = True
                
                args.kind = 'error'
                args.title = None
                args.auto = True
                result = cmd_cap(args)
            except Exception as e:
                # Si hay error al procesar el argumento, sugerir usar stdin
                print(
                    "Error procesando mensaje como argumento. "
                    "Para texto largo o con caracteres especiales, usa stdin:\n"
                    "  dia E --data-root ./data --area it < archivo.txt\n"
                    "  o con heredoc:\n"
                    "  dia E --data-root ./data --area it << 'EOF'\n"
                    "  [tu texto aquí]\n"
                    "  EOF",
                    file=sys.stderr
                )
                raise
            finally:
                # Restaurar stdin
                sys.stdin = original_stdin
            return result
        else:
            # Comportamiento normal: leer desde stdin
            args.kind = 'error'
            args.title = None
            args.auto = True
            return cmd_cap(args)
    
    e_parser.set_defaults(func=cmd_e)

    fix_parser = subparsers.add_parser(
        "fix", help="Linkea fix a error capturado", parents=[common]
    )
    fix_parser.add_argument("--from", dest="from_capture", required=False, help="Capture ID especifico (default: ultimo sin fix)")
    fix_parser.add_argument("--title", required=True, help="Descripcion del fix")
    fix_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    fix_parser.set_defaults(func=cmd_fix)

    fix_commit_parser = subparsers.add_parser(
        "fix-commit", help="Linkea fix a commit SHA", parents=[common]
    )
    fix_commit_parser.add_argument("--fix", dest="fix_id", required=True, help="Fix ID (ej: fix_abc123)")
    fix_commit_group = fix_commit_parser.add_mutually_exclusive_group(required=True)
    fix_commit_group.add_argument("--commit", help="SHA del commit")
    fix_commit_group.add_argument("--last", action="store_true", help="Usar HEAD del repo actual")
    fix_commit_parser.add_argument("--repo", required=False, help="Path del repo (default: cwd)")
    fix_commit_parser.set_defaults(func=cmd_fix_commit)

    update_parser = subparsers.add_parser(
        "update", help="Reinstala la CLI en modo editable"
    )
    update_parser.set_defaults(func=cmd_update)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
