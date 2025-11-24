from __future__ import annotations

import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

from .schemas import AgentSpec, RunRequest


def _parse_entrypoint(entrypoint: str) -> Tuple[str, str]:
    """
    Split 'module.path:AttrName' into ('module.path', 'AttrName').
    """
    if ":" not in entrypoint:
        raise ValueError(f"Invalid entrypoint {entrypoint!r}, expected 'module:attr'")
    module_path, attr_name = entrypoint.split(":", 1)
    module_path = module_path.strip()
    attr_name = attr_name.strip()
    if not module_path or not attr_name:
        raise ValueError(f"Invalid entrypoint {entrypoint!r}, expected 'module:attr'")
    return module_path, attr_name


def _ensure_repo_checked_out(repo_url: str, commit: str | None, dest_dir: Path) -> None:
    """
    Clone or update a git repository into dest_dir.

    Requires git to be installed on the system.
    """
    dest_dir.parent.mkdir(parents=True, exist_ok=True)

    if not dest_dir.exists():
        # Clone
        subprocess.run(
            ["git", "clone", repo_url, str(dest_dir)],
            check=True,
        )
    else:
        # Fetch updates
        subprocess.run(
            ["git", "-C", str(dest_dir), "fetch"],
            check=True,
        )

    if commit:
        # Check out specific commit
        subprocess.run(
            ["git", "-C", str(dest_dir), "checkout", commit],
            check=True,
        )
    else:
        # Stay on HEAD
        subprocess.run(
            ["git", "-C", str(dest_dir), "checkout", "HEAD"],
            check=True,
        )


def run_agent_locally(
    agent: AgentSpec,
    request: RunRequest,
    workdir: Path | None = None,
) -> Dict[str, Any]:
    """
    Run an agent implementation locally based on its spec.

    This is the backend equivalent of 'run-local' in the CLI.
    """
    git_repo = agent.git_repo
    git_commit = agent.git_commit or None
    entrypoint = agent.entrypoint

    if not git_repo:
        raise RuntimeError("Agent does not specify git_repo; cannot run locally.")
    if not entrypoint:
        raise RuntimeError("Agent does not specify entrypoint; cannot run locally.")

    # Decide checkout path
    if workdir is None:
        # Allow override via env, otherwise use ~/.academy/agents
        root = os.getenv("AGENTS_WORKDIR")
        workdir = Path(root) if root else Path.home() / ".academy" / "agents"

    agent_name = agent.name or "unknown-agent"
    dest_dir = workdir / agent_name

    # Clone or update repo
    _ensure_repo_checked_out(git_repo, git_commit, dest_dir)

    # Put repo on sys.path so imports can find it
    repo_path_str = str(dest_dir.resolve())
    if repo_path_str not in sys.path:
        sys.path.insert(0, repo_path_str)

    module_path, attr_name = _parse_entrypoint(entrypoint)

    module = importlib.import_module(module_path)
    target_obj = getattr(module, attr_name)

    inputs = request.inputs or {}

    # Call convention: if it's a class, instantiate and call run(**inputs).
    # If it's a function, call function(**inputs).
    if isinstance(target_obj, type):
        instance = target_obj()
        if not hasattr(instance, "run"):
            raise RuntimeError(f"Entry class {attr_name} has no .run() method")
        result = instance.run(**inputs)
    else:
        result = target_obj(**inputs)

    if not isinstance(result, dict):
        raise RuntimeError("Agent run() must return a dict for now.")

    return result
