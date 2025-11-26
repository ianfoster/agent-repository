# backend/app/runtime.py
from __future__ import annotations

import os
import shutil
import importlib
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .schemas import AgentCard, RunRequest
from .models import AgentImplementation, Location


def _ensure_repo_checked_out(repo_url: str, commit: Optional[str], dest_dir: Path) -> None:
    """
    Clone or update a git repository into dest_dir.

    This will be the same logic you used before (git clone / git fetch).
    """
    import subprocess

    dest_dir.parent.mkdir(parents=True, exist_ok=True)
    git_dir = dest_dir / ".git"

    if dest_dir.exists() and not git_dir.exists():
        shutil.rmtree(dest_dir)

    if not dest_dir.exists():
        subprocess.run(["git", "clone", repo_url, str(dest_dir)], check=True)
    else:
        subprocess.run(["git", "-C", str(dest_dir), "fetch"], check=True)

    if commit:
        subprocess.run(["git", "-C", str(dest_dir), "checkout", commit], check=True)
    else:
        subprocess.run(["git", "-C", str(dest_dir), "checkout", "HEAD"], check=True)


def stage_agent_code(
    agent: AgentImplementation,
    location: Location,
    workdir: Path,
) -> Path:
    """
    Stage an agent's code on a given location.

    For now, we only support local-style staging, using git + filesystem.
    """
    git_repo = agent.git_repo
    git_commit = agent.git_commit
    if not git_repo:
        raise RuntimeError("Agent does not specify git_repo; cannot deploy.")

    agent_name = agent.name or "unknown-agent"
    loc_name = location.name or "unknown-location"

    dest_dir = workdir / agent_name / loc_name

    if os.getenv("AGENTS_SKIP_GIT", "").lower() in {"1", "true", "yes"}:
        dest_dir.mkdir(parents=True, exist_ok=True)
        return dest_dir

    _ensure_repo_checked_out(git_repo, git_commit, dest_dir)
    return dest_dir


def run_agent_locally_from_staged(
    agent: AgentImplementation,
    request: RunRequest,
    staged_path: Path,
) -> Dict[str, Any]:
    """
    Run an agent's entrypoint class's .run(**inputs) locally.

    This mimics your current prototype behavior, but you could later
    replace this with a full Academy Manager/Exchange launch+call.
    """
    entrypoint = agent.entrypoint
    if not entrypoint:
        raise RuntimeError("Agent has no entrypoint; cannot run.")

    repo_path = str(staged_path.resolve())
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)

    if ":" not in entrypoint:
        raise RuntimeError(f"Invalid entrypoint {entrypoint!r}, expected 'module:Class'.")

    module_path, class_name = entrypoint.split(":", 1)
    module = importlib.import_module(module_path)
    target_cls = getattr(module, class_name)

    inputs = request.inputs or {}

    # In future, you might enforce subclass of academy.agent.Agent with @action
    instance = target_cls()
    if not hasattr(instance, "run"):
        raise RuntimeError(f"Entry class {class_name} has no .run() method")

    result = instance.run(**inputs)
    if not isinstance(result, dict):
        raise RuntimeError("Agent.run must return a dict for now.")
    return result
