from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Tuple

from .client import AgentClient


@dataclass
class LocalRunConfig:
    base_url: str = "http://localhost:8000"
    workdir: Path = Path.home() / ".academy" / "agents"
    inputs_path: Path | None = None  # if None, use {} as inputs
    target: str = "local"            # logical target name, used if you also hit /deploy


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
        # Fetch updates (optional)
        subprocess.run(
            ["git", "-C", str(dest_dir), "fetch"],
            check=True,
        )

    if commit:
        # Check out the specific commit
        subprocess.run(
            ["git", "-C", str(dest_dir), "checkout", commit],
            check=True,
        )
    else:
        # Otherwise, stay on default branch
        subprocess.run(
            ["git", "-C", str(dest_dir), "checkout", "HEAD"],
            check=True,
        )


def _load_inputs(inputs_path: Path | None) -> Dict[str, Any]:
    if inputs_path is None:
        return {}
    if not inputs_path.exists():
        raise FileNotFoundError(f"Inputs file not found: {inputs_path}")
    with inputs_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("Inputs JSON must contain an object at the top level (mapping)")
    return data


def run_local(
    identifier: str,
    cfg: LocalRunConfig,
) -> Dict[str, Any]:
    """
    Run an agent implementation locally based on its spec in the repository.

    identifier: agent id (UUID) or exact name.
    """
    client = AgentClient(base_url=cfg.base_url)

    # Resolve agent by id vs name
    if len(identifier) == 36 and identifier.count("-") == 4:
        agent = client.get_agent(identifier)
    else:
        agent = client.find_agent_by_name(identifier)

    git_repo = agent.get("git_repo")
    git_commit = agent.get("git_commit") or None
    entrypoint = agent.get("entrypoint")

    if not git_repo:
        raise RuntimeError("Agent does not specify git_repo; cannot run locally.")
    if not entrypoint:
        raise RuntimeError("Agent does not specify entrypoint; cannot run locally.")

    # Decide checkout path: workdir/<agent-name>
    agent_name = agent.get("name", "unknown-agent")
    dest_dir = cfg.workdir / agent_name

    _ensure_repo_checked_out(git_repo, git_commit, dest_dir)

    # Put repo on sys.path so imports can find it
    repo_path_str = str(dest_dir.resolve())
    if repo_path_str not in sys.path:
        sys.path.insert(0, repo_path_str)

    module_path, attr_name = _parse_entrypoint(entrypoint)

    module = importlib.import_module(module_path)
    target_obj = getattr(module, attr_name)

    # Inputs
    inputs = _load_inputs(cfg.inputs_path)

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

    # Optional: create a stub deployment record with target 'local'
    try:
        client.deploy_agent(agent["id"], target=cfg.target)
    except Exception:
        # Don't fail the run if deployment logging fails
        pass

    return result
