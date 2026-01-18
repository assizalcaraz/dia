from pathlib import Path
from typing import Optional
import hashlib
import os
import subprocess
import sys


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def get_project_id(repo_path: Path) -> str:
    """
    Genera un ID único para el proyecto basado en git remote o path.
    Si hay origin, usa hash de URL. Si no, hash de ruta absoluta.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_path), "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            url = result.stdout.strip()
            return hashlib.sha256(url.encode()).hexdigest()[:16]
    except Exception:
        pass
    
    # Fallback: hash de ruta absoluta
    abs_path = str(repo_path.resolve())
    return hashlib.sha256(abs_path.encode()).hexdigest()[:16]


def data_root(override: Optional[str] = None, repo_path: Optional[Path] = None) -> Path:
    """
    Determina el data_root según Opción B2 (híbrido):
    1. Si override existe, usarlo (soberanía explícita)
    2. Si no, buscar .dia/ en repo_path (si se proporciona)
    3. Si no existe .dia/, usar data global según OS
    """
    if override:
        return Path(override).expanduser().resolve()
    
    # Buscar .dia/ en el repo si se proporciona repo_path
    if repo_path:
        repo_path = Path(repo_path).expanduser().resolve()
        dia_local = repo_path / ".dia"
        if dia_local.exists() and dia_local.is_dir():
            return dia_local
    
    # Fallback: data global según OS
    if os.name == "nt":  # Windows
        appdata = os.getenv("APPDATA", "")
        if appdata:
            return Path(appdata) / "dia"
        return Path.home() / "AppData" / "Roaming" / "dia"
    elif sys.platform == "darwin":  # macOS
        return Path.home() / "Library" / "Application Support" / "dia"
    else:  # Linux y otros Unix
        xdg_data_home = os.getenv("XDG_DATA_HOME", "")
        if xdg_data_home:
            return Path(xdg_data_home) / "dia"
        return Path.home() / ".local" / "share" / "dia"


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


def docs_temp_dir(root: Path) -> Path:
    """Directorio para documentación temporal (fuera del repo)."""
    return root / "docs_temp"


def show_data_root(root: Path) -> str:
    """Retorna string descriptivo del data_root actual (para claridad)."""
    return str(root.resolve())


def ensure_data_dirs(root: Path) -> None:
    """
    Crea estructura mínima de directorios sin fallar.
    Modo 'primer uso': crea directorios vacíos si no existen.
    """
    index_dir(root).mkdir(parents=True, exist_ok=True)
    bitacora_dir(root).mkdir(parents=True, exist_ok=True)
    artifacts_dir(root).mkdir(parents=True, exist_ok=True)
    captures_dir(root).mkdir(parents=True, exist_ok=True)
    analysis_dir(root).mkdir(parents=True, exist_ok=True)
    docs_temp_dir(root).mkdir(parents=True, exist_ok=True)
    # Crear directorio de reglas si no existe
    rules_dir = root / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    # Crear directorio de snapshots si no existe
    snapshots_dir = artifacts_dir(root) / "snapshots"
    snapshots_dir.mkdir(parents=True, exist_ok=True)
    # Crear directorio de propuestas si no existe
    proposals_dir = artifacts_dir(root) / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)
