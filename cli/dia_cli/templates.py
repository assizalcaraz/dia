from __future__ import annotations

from typing import Iterable


def session_start_template(
    day_id: str,
    session_id: str,
    intent: str,
    dod: str,
    mode: str,
    repo_path: str,
    branch: str,
    start_sha: str,
) -> str:
    return (
        f"# BITACORA {day_id} {session_id}\n\n"
        f"- Intent: {intent}\n"
        f"- DoD: {dod}\n"
        f"- Mode: {mode}\n"
        f"- Repo: {repo_path}\n"
        f"- Branch: {branch}\n"
        f"- Start SHA: {start_sha}\n\n"
        "## Trabajo\n\n"
        "- ...\n\n"
        "## Cierre (pendiente)\n\n"
        "- Aciertos:\n"
        "- Fallas:\n"
        "- Decisiones:\n"
        "- Errores repetidos:\n"
        "- Proxima accion:\n"
    )


def cierre_template(
    day_id: str,
    session_id: str,
    summary: str,
    warnings: Iterable[str],
    next_action: str,
) -> str:
    warnings_text = "\n".join(f"- {item}" for item in warnings) or "- Sin alertas"
    return (
        f"# CIERRE {day_id} {session_id}\n\n"
        "## Resumen\n\n"
        f"{summary}\n\n"
        "## Alertas\n\n"
        f"{warnings_text}\n\n"
        "## Proxima accion\n\n"
        f"- {next_action}\n"
    )


def limpieza_template(
    day_id: str, session_id: str, tasks: Iterable[str]
) -> str:
    tasks_text = "\n".join(f"- {item}" for item in tasks) or "- Sin tareas"
    return (
        f"# LIMPIEZA {day_id} {session_id}\n\n"
        "## Tareas\n\n"
        f"{tasks_text}\n"
    )
