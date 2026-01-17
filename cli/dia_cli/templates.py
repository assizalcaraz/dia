from __future__ import annotations

from typing import Any, Iterable


def jornada_template(day_id: str) -> str:
    """Plantilla inicial para bitácora de jornada (archivo único por día)."""
    return (
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
    """Template legacy - mantenido para compatibilidad, pero ya no se usa."""
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


def session_auto_section_template(
    session_id: str,
    start_ts: str,
    intent: str,
    dod: str,
    mode: str,
    repo_path: str,
    branch: str,
    start_sha: str,
) -> str:
    """Sección automática de sesión para agregar a bitácora de jornada."""
    sha_display = start_sha or "(sin commits)"
    return (
        f"### Sesión {session_id}\n"
        f"- start: {start_ts}\n"
        f"- intent: {intent}\n"
        f"- dod: {dod}\n"
        f"- mode: {mode}\n"
        f"- repo: {repo_path}\n"
        f"- branch: {branch}\n"
        f"- start_sha: {sha_display}\n"
        f"- end: (pendiente)\n"
        f"- commits: (pendiente)\n"
        f"- eventos:\n\n"
        "#### Eventos\n"
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


def daily_summary_template(
    day_id: str,
    objective: str,
    attempted: str,
    achieved: str,
    not_achieved: str,
    deviations: Iterable[str],
) -> str:
    """Plantilla para resumen del día (sección 5 de bitácora)."""
    deviations_text = "\n".join(f"- {item}" for item in deviations) or "- Sin desvíos detectados"
    return (
        f"## 5. Resumen del día (generado)\n\n"
        f"- Qué se intentó: {attempted}\n"
        f"- Qué se logró realmente: {achieved}\n"
        f"- Qué no se logró y por qué: {not_achieved}\n"
        f"- Desvíos detectados:\n{deviations_text}\n"
    )


def analysis_vs_objective_template(
    day_id: str,
    objective: str,
    expected_plan: str,
    actual_result: str,
    gaps: Iterable[str],
    impact: str,
    suggested_adjustments: Iterable[str],
) -> str:
    """Plantilla para análisis comparativo vs objetivo."""
    gaps_text = "\n".join(f"- {item}" for item in gaps) or "- Sin brechas"
    adjustments_text = "\n".join(f"- {item}" for item in suggested_adjustments) or "- Sin ajustes sugeridos"
    return (
        f"# Análisis {day_id} vs Objetivo\n\n"
        f"## Objetivo declarado\n{objective}\n\n"
        f"## Plan esperado\n{expected_plan}\n\n"
        f"## Resultado real\n{actual_result}\n\n"
        f"## Brechas\n{gaps_text}\n\n"
        f"## Impacto\n{impact}\n\n"
        f"## Ajustes sugeridos\n{adjustments_text}\n"
    )


def rolling_summary_template(
    day_id: str,
    timestamp: str,
    assessment: str,
    objective: str,
    next_step: str,
    blocker: str | None,
    risks: Iterable[str],
    delta: dict[str, Any],
) -> str:
    """Plantilla para resumen rolling (regenerable durante el día)."""
    risks_text = "\n".join(f"- {item}" for item in risks) or "- Sin riesgos detectados"
    blocker_text = f"\n\n## Blocker\n\n{blocker}\n" if blocker else ""
    
    assessment_emoji = {
        "ON_TRACK": "✅",
        "OFF_TRACK": "⚠️",
        "BLOCKED": "🚫",
    }.get(assessment, "❓")
    
    delta_text = ""
    if delta.get("new_events"):
        delta_text = f"\n\n## Cambios desde último resumen\n\n"
        delta_text += f"- Nuevos eventos: {len(delta['new_events'])}\n"
        delta_text += f"- Nuevos commits: {delta.get('new_commits', 0)}\n"
        delta_text += f"- Nuevos errores: {delta.get('new_errors', 0)}\n"
        if delta.get("assessment_changed"):
            delta_text += f"- Estado cambió: {delta.get('assessment_changed')}\n"
    
    return (
        f"# Resumen Rolling {day_id}\n\n"
        f"**Generado**: {timestamp}\n\n"
        f"## Estado: {assessment_emoji} {assessment}\n\n"
        f"## Objetivo\n{objective}\n\n"
        f"## Próximo paso\n{next_step}\n"
        f"{blocker_text}"
        f"## Riesgos\n{risks_text}"
        f"{delta_text}"
    )


def nightly_summary_template(
    day_id: str,
    timestamp: str,
    assessment: str,
    objective: str,
    next_step: str,
    blocker: str | None,
    risks: Iterable[str],
    delta: dict[str, Any],
) -> str:
    """Plantilla para resumen nightly (generado al final del día)."""
    risks_text = "\n".join(f"- {item}" for item in risks) or "- Sin riesgos detectados"
    blocker_text = f"\n\n## Blocker\n\n{blocker}\n" if blocker else ""
    
    assessment_emoji = {
        "ON_TRACK": "✅",
        "OFF_TRACK": "⚠️",
        "BLOCKED": "🚫",
    }.get(assessment, "❓")
    
    return (
        f"# Resumen Nightly {day_id}\n\n"
        f"**Generado**: {timestamp}\n\n"
        f"## Estado final: {assessment_emoji} {assessment}\n\n"
        f"## Objetivo del día\n{objective}\n\n"
        f"## Próximo paso (mañana)\n{next_step}\n"
        f"{blocker_text}"
        f"## Riesgos acumulados\n{risks_text}\n"
    )
