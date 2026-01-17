from pathlib import Path
from typing import Optional


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def data_root(override: Optional[str] = None) -> Path:
    if override:
        return Path(override).expanduser().resolve()
    return repo_root() / "data"


def index_dir(root: Path) -> Path:
    return root / "index"


def bitacora_dir(root: Path) -> Path:
    return root / "bitacora"


def artifacts_dir(root: Path) -> Path:
    return root / "artifacts"


def captures_dir(root: Path) -> Path:
    return artifacts_dir(root) / "captures"


def rules_path(root: Path) -> Path:
    return root / "rules.json"


def analysis_dir(root: Path) -> Path:
    return root / "analysis"


def summaries_artifacts_dir(root: Path, day_id: str) -> Path:
    return artifacts_dir(root) / "summaries" / day_id


def ensure_data_dirs(root: Path) -> None:
    index_dir(root).mkdir(parents=True, exist_ok=True)
    bitacora_dir(root).mkdir(parents=True, exist_ok=True)
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    captures_dir(root).mkdir(parents=True, exist_ok=True)
    analysis_dir(root).mkdir(parents=True, exist_ok=True)
