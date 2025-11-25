from __future__ import annotations

import shutil
import importlib
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

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
        # Otherwise, stay on current HEAD
        subprocess.run(
            ["git", "-C", str(dest_dir), "checkout", "HEAD"],
            check=True,
        )



def stage_agent_code(agent: AgentSpec, workdir: Path, target: str) -> Path:
    """
    Stage an agent's code locally by cloning/updating its git_repo.

    Returns the path to the staged code for this agent/target combination.
    """
    git_repo = agent.git_repo
    git_commit = agent.git_commit or None
    if not git_repo:
        raise RuntimeError("Agent does not specify git_repo; cannot deploy.")

    # e.g., ~/.academy/agents/<agent-name>/<target>
    agent_name = agent.name or "unknown-agent"
    dest_dir = workdir / agent_name / target
    git_dir = dest_dir / ".git"

    # Skip git operations in tests if AGENTS_SKIP_GIT is set
    if os.getenv("AGENTS_SKIP_GIT", "").lower() in {"1", "true", "yes"}:
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir

    # If the directory exists but is not a git repo, remove it and reclone cleanly.
    if dest_dir.exists() and not git_dir.exists():
        shutil.rmtree(dest_dir)

    _ensure_repo_checked_out(git_repo, git_commit, dest_dir)
    return dest_dir

def run_agent_locally_from_staged(
    agent: AgentSpec,
    request: RunRequest,
    staged_path: Path,
) -> Dict[str, Any]:
    """
    Run an agent using code staged at staged_path.

    This does NOT perform any git operations; it assumes the code has already
    been cloned/updated by a prior deployment.
    """
    entrypoint = agent.entrypoint
    if not entrypoint:
        raise RuntimeError("Agent does not specify entrypoint; cannot run locally.")

    # Make staged repo importable
    repo_path_str = str(staged_path.resolve())
    if repo_path_str not in sys.path:
        sys.path.insert(0, repo_path_str)

    module_path, attr_name = _parse_entrypoint(entrypoint)

    module = importlib.import_module(module_path)
    target_obj = getattr(module, attr_name)

    inputs: Dict[str, Any] = request.inputs or {}

    # If it's a class, instantiate and call .run(**inputs)
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
