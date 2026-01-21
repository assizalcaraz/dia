# Módulo: `git_ops.py`

**Ubicación**: `cli/dia_cli/git_ops.py`  
**Propósito**: Operaciones Git para obtener información del repositorio (SHA, branch, status, diff, log, changed files).

---

## Funciones Públicas

### `run_git(repo_path: Path, args: Iterable[str]) -> str`

Ejecuta un comando Git y retorna la salida.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.
- `args` (Iterable[str]): Argumentos del comando Git (sin `git`).

**Retorna**: `str` — Salida estándar del comando.

**Lanza**: `RuntimeError` si el comando falla (código de salida != 0).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import run_git

repo = Path("/ruta/al/repo")
branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
```

---

### `is_git_repo(repo_path: Path) -> bool`

Verifica si un directorio es un repositorio Git válido.

**Parámetros**:
- `repo_path` (Path): Ruta del directorio a verificar.

**Retorna**: `bool` — `True` si es un repo Git válido, `False` en caso contrario.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import is_git_repo

repo = Path("/ruta/al/repo")
if is_git_repo(repo):
    print("Es un repo Git válido")
```

---

### `head_sha(repo_path: Path) -> Optional[str]`

Obtiene el SHA del commit HEAD.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `Optional[str]` — SHA del HEAD, o `None` si el repo no tiene commits.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import head_sha

repo = Path("/ruta/al/repo")
sha = head_sha(repo)
if sha:
    print(f"HEAD: {sha}")
else:
    print("Repo sin commits")
```

---

### `current_branch(repo_path: Path) -> str`

Obtiene el nombre de la rama actual.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `str` — Nombre de la rama actual.

**Nota**: Si falla `rev-parse --abbrev-ref`, intenta `symbolic-ref --short`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import current_branch

repo = Path("/ruta/al/repo")
branch = current_branch(repo)
print(f"Rama actual: {branch}")
```

---

### `status_porcelain(repo_path: Path) -> str`

Obtiene el estado del working tree en formato porcelain.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `str` — Salida de `git status --porcelain`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import status_porcelain

repo = Path("/ruta/al/repo")
status = status_porcelain(repo)
if status:
    print("Repo tiene cambios")
```

---

### `diff(repo_path: Path, ref_range: Optional[str] = None) -> str`

Obtiene el diff del repositorio.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.
- `ref_range` (Optional[str]): Rango de commits (ej: `"abc123..def456"`). Si es `None`, retorna diff del working tree.

**Retorna**: `str` — Salida de `git diff`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import diff

repo = Path("/ruta/al/repo")
# Diff del working tree
working_diff = diff(repo)

# Diff entre commits
commit_diff = diff(repo, "abc123..def456")
```

---

### `log_oneline(repo_path: Path, ref_range: str) -> str`

Obtiene el log de commits en formato oneline.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.
- `ref_range` (str): Rango de commits (ej: `"abc123..HEAD"`).

**Retorna**: `str` — Salida de `git log --oneline`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import log_oneline

repo = Path("/ruta/al/repo")
commits = log_oneline(repo, "abc123..HEAD")
print(commits)
```

---

### `changed_files(repo_path: Path, ref_range: str) -> list[str]`

Obtiene la lista de archivos modificados en un rango de commits.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.
- `ref_range` (str): Rango de commits (ej: `"abc123..HEAD"`).

**Retorna**: `list[str]` — Lista de rutas de archivos modificados.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import changed_files

repo = Path("/ruta/al/repo")
files = changed_files(repo, "abc123..HEAD")
for file in files:
    print(file)
```

---

### `tracked_files_count(repo_path: Path) -> int`

Cuenta el número de archivos tracked en el repositorio.

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `int` — Número de archivos tracked.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import tracked_files_count

repo = Path("/ruta/al/repo")
count = tracked_files_count(repo)
print(f"Archivos tracked: {count}")
```

---

### `empty_tree_sha(repo_path: Path) -> str`

Obtiene el SHA del árbol vacío (para repos sin commits).

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `str` — SHA del árbol vacío.

**Nota**: Usa `git hash-object -t tree /dev/null`.

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import empty_tree_sha

repo = Path("/ruta/al/repo")
empty = empty_tree_sha(repo)
# Usar como start_sha para repos sin commits
```

---

### `changed_files_working(repo_path: Path) -> list[str]`

Obtiene la lista de archivos modificados en el working tree (staged + unstaged).

**Parámetros**:
- `repo_path` (Path): Ruta del repositorio Git.

**Retorna**: `list[str]` — Lista de rutas de archivos modificados (ordenada, sin duplicados).

**Ejemplo**:
```python
from pathlib import Path
from dia_cli.git_ops import changed_files_working

repo = Path("/ruta/al/repo")
files = changed_files_working(repo)
for file in files:
    print(file)
```

---

## Manejo de Errores

Todas las funciones que ejecutan comandos Git lanzan `RuntimeError` si el comando falla. Las funciones que pueden retornar `None` (como `head_sha`) manejan repos sin commits de forma segura.

**Ejemplo de manejo**:
```python
from pathlib import Path
from dia_cli.git_ops import head_sha, run_git

repo = Path("/ruta/al/repo")

# Manejo seguro de repos sin commits
sha = head_sha(repo)
if sha is None:
    print("Repo sin commits")

# Manejo de errores en comandos
try:
    branch = run_git(repo, ["rev-parse", "--abbrev-ref", "HEAD"])
except RuntimeError as e:
    print(f"Error: {e}")
```

---

## Dependencias

- **Módulo estándar**: `subprocess` (para ejecutar comandos Git)
- **Módulo estándar**: `pathlib` (para rutas)

---

## Notas de Implementación

- Todas las funciones ejecutan comandos Git usando `subprocess.run` con `-C` para especificar el directorio del repo.
- Los comandos se ejecutan con `check=False` y se captura la salida estándar.
- Si un comando falla, se lanza `RuntimeError` con el mensaje de error.
- Las funciones que pueden fallar (como `head_sha`) retornan `None` en lugar de lanzar excepciones para manejar repos sin commits.

---

## Referencias

- [Guía de `dia start`](../../guides/dia-start.md)
- [Guía de `dia end`](../../guides/dia-end.md)
- [Documentación de módulos CLI](README.md)
