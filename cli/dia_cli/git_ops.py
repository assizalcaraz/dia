from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, Optional


def run_git(repo_path: Path, args: Iterable[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout.strip()


def is_git_repo(repo_path: Path) -> bool:
    try:
        output = run_git(repo_path, ["rev-parse", "--is-inside-work-tree"])
        return output == "true"
    except RuntimeError:
        return False


def head_sha(repo_path: Path) -> Optional[str]:
    try:
        return run_git(repo_path, ["rev-parse", "HEAD"])
    except RuntimeError:
        return None


def current_branch(repo_path: Path) -> str:
    try:
        return run_git(repo_path, ["rev-parse", "--abbrev-ref", "HEAD"])
    except RuntimeError:
        return run_git(repo_path, ["symbolic-ref", "--short", "HEAD"])


def status_porcelain(repo_path: Path) -> str:
    return run_git(repo_path, ["status", "--porcelain"])


def diff(repo_path: Path, ref_range: Optional[str] = None) -> str:
    if ref_range:
        return run_git(repo_path, ["diff", ref_range])
    return run_git(repo_path, ["diff"])


def log_oneline(repo_path: Path, ref_range: str) -> str:
    return run_git(repo_path, ["log", "--oneline", ref_range])


def changed_files(repo_path: Path, ref_range: str) -> list[str]:
    output = run_git(repo_path, ["diff", "--name-only", ref_range])
    if not output:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def tracked_files_count(repo_path: Path) -> int:
    output = run_git(repo_path, ["ls-files"])
    if not output:
        return 0
    return len(output.splitlines())


def empty_tree_sha(repo_path: Path) -> str:
    return run_git(repo_path, ["hash-object", "-t", "tree", "/dev/null"])


def changed_files_working(repo_path: Path) -> list[str]:
    staged = run_git(repo_path, ["diff", "--name-only", "--cached"])
    unstaged = run_git(repo_path, ["diff", "--name-only"])
    files = set()
    for output in (staged, unstaged):
        if not output:
            continue
        files.update(line.strip() for line in output.splitlines() if line.strip())
    return sorted(files)
