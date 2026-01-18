import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Optional


def now_iso() -> str:
    return datetime.now().astimezone().isoformat()


def day_id() -> str:
    return datetime.now().astimezone().date().isoformat()


def read_json_lines(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return []
    lines: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            lines.append(json.loads(line))
    return lines


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_text(path: Path) -> str:
    """Lee contenido de archivo, retorna string vacío si no existe."""
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def append_to_jornada_auto_section(path: Path, content: str) -> None:
    """
    Agrega contenido a la sección automática (3) de la bitácora de jornada.
    Si el archivo no existe, crea la estructura inicial.
    Si existe, agrega al final de la sección automática (después del separador ---).
    """
    if not path.exists():
        # Crear estructura inicial
        from .templates import jornada_template
        day = path.stem  # YYYY-MM-DD del nombre del archivo
        initial = jornada_template(day)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(initial + content, encoding="utf-8")
        return
    
    text = read_text(path)
    
    # Buscar el separador "---" que marca el inicio de sección automática
    separator = "---\n\n## 3. Registro automático (NO EDITAR)"
    
    if separator in text:
        # Agregar al final del contenido existente (append-only)
        path.write_text(text + "\n" + content, encoding="utf-8")
    else:
        # No hay separador, agregar sección automática
        separator_line = "\n---\n\n## 3. Registro automático (NO EDITAR)\n(append-only, escrito por /dia)\n\n"
        path.write_text(text + separator_line + content, encoding="utf-8")


def compute_content_hash(content: str) -> str:
    """Calcula SHA256 del contenido para detectar errores repetidos."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_last_unfixed_capture(
    events_path: Path, session_id: Optional[str] = None, day_id: Optional[str] = None
) -> Optional[dict[str, Any]]:
    """
    Busca el último CaptureCreated sin FixLinked asociado.
    Si se proporciona session_id, busca solo en esa sesión.
    Si se proporciona day_id, busca solo en ese día.
    
    Usa error_event_id para asociar FixLinked a CaptureCreated específicos,
    permitiendo que errores con el mismo hash tengan fixes independientes.
    """
    events = list(read_json_lines(events_path))
    
    # Filtrar por día si se especifica
    if day_id:
        events = [e for e in events if e.get("session", {}).get("day_id") == day_id]
    
    # Filtrar por sesión si se especifica
    if session_id:
        events = [e for e in events if e.get("session", {}).get("session_id") == session_id]
    
    # Recopilar todos los CaptureCreated
    captures: list[dict[str, Any]] = []
    for event in events:
        if event.get("type") == "CaptureCreated":
            error_hash = event.get("payload", {}).get("error_hash")
            if error_hash:
                captures.append(event)
    
    # Recopilar todos los FixLinked usando error_event_id (más preciso que error_hash)
    fixed_event_ids: set[str] = set()
    for event in events:
        if event.get("type") == "FixLinked":
            error_event_id = event.get("payload", {}).get("error_event_id")
            if error_event_id:
                fixed_event_ids.add(error_event_id)
    
    # Encontrar el último CaptureCreated sin fix (usando event_id específico)
    unfixed = [
        capture 
        for capture in captures 
        if capture.get("event_id") not in fixed_event_ids
    ]
    
    if not unfixed:
        return None
    
    # Ordenar por timestamp y retornar el más reciente
    unfixed.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return unfixed[0]
