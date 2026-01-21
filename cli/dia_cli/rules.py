import json
from pathlib import Path
from typing import Any


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merge profundo: combina base y override recursivamente.
    Si override tiene una clave, reemplaza base (o mergea si ambos son dicts).
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_rules(path: Path) -> dict[str, Any]:
    """
    Carga reglas de gobernanza documental y repo:
    1. Carga defaults desde cli/dia_cli/default_rules/rules.json (versionado)
    2. Si existe path (data_root/rules.json), mergea (override del usuario)
    3. Si no existe default, usa estructura mínima como fallback
    """
    # Cargar defaults versionados
    default_rules_path = Path(__file__).parent / "default_rules" / "rules.json"
    default_rules: dict[str, Any] = {}
    if default_rules_path.exists():
        with default_rules_path.open("r", encoding="utf-8") as handle:
            default_rules = json.load(handle)
    
    # Cargar override del usuario si existe
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            override_rules = json.load(handle)
            # Merge profundo: override gana sobre defaults
            default_rules = _deep_merge(default_rules, override_rules)
    
    return default_rules


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
