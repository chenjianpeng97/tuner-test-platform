import subprocess  # noqa: S404
from pathlib import Path
from shutil import which


class GitSyncService:
    def __init__(self) -> None:
        git_bin = which("git")
        if git_bin is None:
            raise RuntimeError("git executable not found")
        self._git_bin = git_bin

    def _run(self, args: list[str]) -> None:
        subprocess.run(  # noqa: S603
            args,
            check=True,
            capture_output=True,
            text=True,
        )

    def clone(self, *, repo_url: str, branch: str, dst_path: Path) -> None:
        self._run([self._git_bin, "clone", "--branch", branch, repo_url, str(dst_path)])

    def pull(self, *, repo_path: Path) -> None:
        self._run([self._git_bin, "-C", str(repo_path), "pull"])

    def commit(self, *, repo_path: Path, message: str) -> None:
        self._run([self._git_bin, "-C", str(repo_path), "commit", "-m", message])

    def push(self, *, repo_path: Path) -> None:
        self._run([self._git_bin, "-C", str(repo_path), "push"])

    def add(self, *, repo_path: Path, paths: list[str]) -> None:
        self._run([self._git_bin, "-C", str(repo_path), "add", "--", *paths])

    def reset_hard(self, *, repo_path: Path, ref: str) -> None:
        self._run([self._git_bin, "-C", str(repo_path), "reset", "--hard", ref])
