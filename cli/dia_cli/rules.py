import json
from pathlib import Path
from typing import Any

DEFAULT_RULES: dict[str, Any] = {
    "protected_branches": ["main", "master", "production", "prod"],
    "commit_tag": "[dia]",
    "commit_types": ["feat", "fix", "refactor", "docs", "test", "chore", "wip"],
    "suspicious_patterns": [
        {"pattern": "docs/scratch/", "rule": "docs_scratch"},
        {"pattern": "_test.py", "rule": "test_outside_tests"},
    ],
    "documentation_scopes": {
        "cli_commands": {
            "description": "Documentación de comandos CLI",
            "paths": [
                "docs/guides/dia-*.md",
                "docs/manual/CAPTURA_ERRORES.md",
                "docs/modules/cli/*.md"
            ],
            "triggers": [
                "cambios en cli/dia_cli/*.py",
                "nuevos comandos CLI",
                "cambios en argumentos de comandos",
                "cambios en comportamiento de comandos"
            ]
        },
        "ui_components": {
            "description": "Documentación de componentes UI",
            "paths": [
                "docs/modules/components/*.md",
                "docs/modules/ui/*.md"
            ],
            "triggers": [
                "cambios en ui/src/components/*.svelte",
                "nuevos componentes",
                "cambios en props o comportamiento de componentes"
            ]
        },
        "api_endpoints": {
            "description": "Documentación de API",
            "paths": [
                "docs/modules/api/*.md",
                "docs/guides/api-*.md"
            ],
            "triggers": [
                "cambios en server/api/*.py",
                "nuevos endpoints",
                "cambios en estructura de respuestas"
            ]
        },
        "workflows": {
            "description": "Documentación de flujos de trabajo",
            "paths": [
                "docs/guides/*.md",
                "docs/README.md"
            ],
            "triggers": [
                "cambios en flujos documentados",
                "nuevos workflows",
                "actualizaciones de procesos"
            ]
        },
        "architecture": {
            "description": "Documentación de arquitectura y diseño",
            "paths": [
                "docs/overview/*.md",
                "docs/specs/*.md",
                "docs/RESUMEN_DISENO_DIA.md",
                "docs/ESTADO_ACTUAL.md"
            ],
            "triggers": [
                "cambios arquitectónicos significativos",
                "nuevas decisiones de diseño",
                "actualizaciones de estado del proyecto"
            ]
        }
    }
}


def load_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_RULES
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_repo_structure_rules(data_root: Path) -> dict[str, Any]:
    """
    Carga reglas de estructura del repo:
    1. Carga defaults desde cli/dia_cli/default_rules/repo_structure.json (versionado)
    2. Si existe data_root/rules/repo_structure.json, mergea (override)
    """
    # Cargar defaults
    default_rules_path = Path(__file__).parent / "default_rules" / "repo_structure.json"
    default_rules = {}
    if default_rules_path.exists():
        with default_rules_path.open("r", encoding="utf-8") as handle:
            default_rules = json.load(handle)
    
    # Cargar override si existe
    override_path = data_root / "rules" / "repo_structure.json"
    if override_path.exists():
        with override_path.open("r", encoding="utf-8") as handle:
            override_rules = json.load(handle)
            # Mergear: si hay reglas con mismo ID, el override gana
            if "rules" in override_rules:
                default_rules_list = default_rules.get("rules", [])
                override_rules_list = override_rules.get("rules", [])
                # Crear dict por ID para mergear
                rules_dict = {r.get("id"): r for r in default_rules_list}
                rules_dict.update({r.get("id"): r for r in override_rules_list})
                default_rules["rules"] = list(rules_dict.values())
    
    return default_rules
