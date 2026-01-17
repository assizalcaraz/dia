from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path
import subprocess
from typing import Any, Optional

from . import config
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
from .utils import day_id, now_iso, read_json_lines, write_text


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
    path = config.bitacora_dir(root) / day / f"{session_id}.md"
    content = session_start_template(
        day, session_id, intent, dod, mode, repo_path, branch, start_sha
    )
    write_text(path, content)
    return path


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

    session_id = next_session_id(day_id(), sessions_path)
    actor = _actor_from_args(args)
    project = _project_from_args(args)

    branch = current_branch(repo_path)
    start_sha = head_sha(repo_path)
    if start_sha is None:
        print("Repo sin commits. Continuando en modo inicial.")
    repo_state = _repo_payload(repo_path, branch, start_sha)

    session = _session_payload(args, session_id)
    start_event = _build_event(
        "SessionStarted",
        session=session,
        actor=actor,
        project=project,
        repo=repo_state,
        payload={"cmd": "dia start"},
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
    message = _suggest_commit_message(session_id, rules, files)
    # Usar git-commit-cursor para commits de Cursor/IA (autoría identificable)
    cli_root = Path(__file__).resolve().parents[1]
    commit_cursor_path = cli_root / "git-commit-cursor"
    if commit_cursor_path.exists():
        command = f'git-commit-cursor -m "{message}"'
    else:
        # Fallback si no está en PATH
        command = f'{commit_cursor_path} -m "{message}"'

    event = _build_event(
        "CommitSuggestionIssued",
        session={"day_id": current["session"]["day_id"], "session_id": session_id},
        actor=_actor_from_args(args),
        project=_project_from_args(args),
        repo=_repo_payload(repo_path, current_branch(repo_path), start_sha),
        payload={"command": command, "files": files},
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

    summary = f"{commit_count} commits, {len(files)} archivos tocados."
    cierre_path = config.bitacora_dir(root) / session["day_id"] / f"CIERRE_{session_id}.md"
    limpieza_path = (
        config.bitacora_dir(root) / session["day_id"] / f"LIMPIEZA_{session_id}.md"
    )
    write_text(cierre_path, cierre_template(session["day_id"], session_id, summary, [], "Revisar limpieza"))
    write_text(limpieza_path, limpieza_template(session["day_id"], session_id, tasks))

    print(f"Sesion {session_id} cerrada. Cierre: {cierre_path}")
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
