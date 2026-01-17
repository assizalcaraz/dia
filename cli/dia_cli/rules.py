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
}


def load_rules(path: Path) -> dict[str, Any]:
    if not path.exists():
        return DEFAULT_RULES
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
