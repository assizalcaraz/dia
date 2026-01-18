from __future__ import annotations

import argparse
import json
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
    status_porcelain,
    tracked_files_count,
)
from .ndjson import append_line
from .rules import load_rules
from .sessions import current_session, next_session_id
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

    root = config.data_root(args.data_root)
    config.ensure_data_dirs(root)
    sessions_path = _sessions_path(root)
    events_path = _events_path(root)

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

    print(f"Sesion {session_id} iniciada. Bitacora: {bitacora_path}")
    return 0


def cmd_pre_feat(args: argparse.Namespace) -> int:
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root)
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
    root = config.data_root(args.data_root)
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
    
    print(f"Sesion {session_id} cerrada. Bitacora jornada: {jornada_path}")
    return 0


def cmd_close_day(args: argparse.Namespace) -> int:
    """Cierra la jornada (ritual humano). Solo registra evento DayClosed."""
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
    print("Nota: Para generar resúmenes, ejecuta 'dia summarize --mode rolling' o 'dia summarize --mode nightly'")
    return 0


def cmd_summarize(args: argparse.Namespace) -> int:
    """Genera resumen regenerable (rolling o nightly)."""
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
    
    # Leer bitácora para extraer objetivo
    jornada_path = config.bitacora_dir(root) / f"{day_id_val}.md"
    objective = extract_objective(jornada_path)
    
    # Ruta del índice de resúmenes (summaries.ndjson)
    summaries_path = config.index_dir(root) / "summaries.ndjson"
    
    # Generar resumen
    summary_data = generate_summary(
        root=root,
        day_id_val=day_id_val,
        mode=args.mode,
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
    
    print(f"Resumen {args.mode} generado para {day_id_val}")
    print(f"Assessment: {summary_data['payload']['assessment']}")
    print(f"Próximo paso: {summary_data['payload']['next_step']}")
    if summary_data['payload'].get('blocker'):
        print(f"Blocker: {summary_data['payload']['blocker']}")
    print(f"Artefacto: {summary_data['payload']['links'][0]['ref']}")
    
    return 0


def cmd_cap(args: argparse.Namespace) -> int:
    """Captura texto (logs/errores) y lo guarda como artifact + evento NDJSON."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root)
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
        print("Analizando error con LLM...", file=sys.stderr)
        generated_title = analyze_error_with_llm(content, args.kind)
        if generated_title:
            title = generated_title
            print(f"Título generado: {title}", file=sys.stderr)
        else:
            # Fallback: usar análisis simple
            title = _analyze_error_simple(content)
            print(f"Título generado (simple): {title}", file=sys.stderr)
    
    if not title:
        print("Error: se requiere --title o usar --auto", file=sys.stderr)
        return 1

    # Calcular hash
    error_hash = compute_content_hash(content)

    # Verificar si ya existe este error
    events = list(read_json_lines(events_path))
    existing_capture = None
    for event in events:
        if event.get("type") == "CaptureCreated":
            if event.get("payload", {}).get("error_hash") == error_hash:
                existing_capture = event
                break

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
        print(f"Error repetido detectado (hash: {error_hash[:8]}...)")
    else:
        print(f"Captura creada: {capture_id}")
    print(f"Artifact: {artifact_path}")
    print(f"Meta: {meta_path}")

    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Linkea un fix a un error capturado."""
    repo_path = Path(args.repo or Path.cwd()).expanduser().resolve()
    root = config.data_root(args.data_root)
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

    fix_event = _build_event(
        "FixLinked",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={
            "error_event_id": error_event_id,
            "error_hash": error_hash,
            "fix_sha": fix_sha,
            "title": title,
        },
    )

    append_line(events_path, fix_event)

    print(f"Fix linkeado a error: {error_hash[:8]}...")
    print(f"Error event_id: {error_event_id}")
    if fix_sha:
        print(f"Fix commit: {fix_sha}")
    else:
        print("Fix en working tree (aun sin commit)")
        print("Ejecuta 'dia pre-feat' para sugerir commit")

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

    start_parser = subparsers.add_parser(
        "start", help="Inicia sesion", parents=[common]
    )
    start_parser.add_argument("--repo", required=False)
    start_parser.add_argument("--intent", required=False)
    start_parser.add_argument("--dod", required=False)
    start_parser.add_argument("--mode", default=None)
    start_parser.set_defaults(func=cmd_start)

    pre_feat_parser = subparsers.add_parser(
        "pre-feat", help="Checkpoint pre-feat", parents=[common]
    )
    pre_feat_parser.add_argument("--repo", required=False)
    pre_feat_parser.set_defaults(func=cmd_pre_feat)

    end_parser = subparsers.add_parser(
        "end", help="Cierra sesion", parents=[common]
    )
    end_parser.add_argument("--repo", required=False)
    end_parser.set_defaults(func=cmd_end)

    close_day_parser = subparsers.add_parser(
        "close-day", help="Cierra jornada (ritual humano)", parents=[common]
    )
    close_day_parser.set_defaults(func=cmd_close_day)

    summarize_parser = subparsers.add_parser(
        "summarize", help="Genera resumen regenerable", parents=[common]
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
    e_parser.add_argument("error_message", nargs="?", help="Mensaje de error (opcional, también se puede pasar por stdin)")
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
