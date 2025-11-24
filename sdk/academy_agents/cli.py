from __future__ import annotations
from .runner import LocalRunConfig, run_local

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List
import json

import yaml

from .client import AgentClient


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("YAML file must contain a mapping at the top level")
    return data


def _write_template_yaml(path: Path) -> None:
    if path.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {path}")
    template = """\
# Minimal agent specification for the Academy Agent Repository
# Fill in the fields you care about; you can leave others blank.
# This YAML will be sent directly to POST /agents.

name: example-agent
version: "0.1.0"
description: >
  Short description of what this agent does (e.g., screens materials,
  sets up simulations, schedules lab experiments).

agent_type: task    # e.g., "task", "domain", "planner", "tool-wrapper"
tags: ["example", "cli"]

owner: your-team-or-username

# GitHub / code metadata
git_repo: https://github.com/your-org/your-agent-repo
git_commit: ""      # optional, you can pin a specific commit SHA
container_image: "" # e.g., ghcr.io/your-org/your-agent:0.1.0
entrypoint: ""      # e.g., agents.materials:MaterialsScreeningAgent

# Schema for inputs / outputs (as the backend expects them)
inputs:
  parameter:
    description: "Example input parameter"
    type: "string"       # string, float, json, file, etc.
    required: true
outputs:
  result:
    description: "Example result"
    type: "float"
    required: true

# Optional A2A Agent Card metadata (simplified)
a2a_card:
  name: example-agent
  url: https://example.org/a2a/example-agent
  description: Example A2A card for this agent.
  version: "0.1.0"
  protocolVersion: "0.2.6"
  capabilities: {}
  skills: []
  defaultInputModes: ["text/plain"]
  defaultOutputModes: ["text/plain"]
  supportsAuthenticatedExtendedCard: false
"""
    path.write_text(template, encoding="utf-8")


def _print_agent_list(agents: List[Dict[str, Any]]) -> None:
    if not agents:
        print("No agents found.")
        return

    # Simple columnar output: id, name, version, type, owner, status
    for a in agents:
        aid = a.get("id", "")
        name = a.get("name", "")
        version = a.get("version", "")
        atype = a.get("agent_type", "")
        owner = a.get("owner") or "-"
        status = a.get("validation_status", "unvalidated")
        print(f"{aid}  {name}  {version}  {atype}  {owner}  {status}")


def _print_agent_detail(agent: Dict[str, Any]) -> None:
    # YAML is a nice human-readable format for nested structures
    print(
        yaml.safe_dump(
            agent,
            sort_keys=False,
            default_flow_style=False,
        )
    )


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="academy-agents",
        description="CLI for interacting with the Academy Agent Repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ------------------------------------------------------------------
    # register
    # ------------------------------------------------------------------
    register_parser = subparsers.add_parser(
        "register",
        help="Register an agent from an agent.yaml file",
    )
    register_parser.add_argument(
        "path",
        type=str,
        help="Path to an agent.yaml file describing the agent",
    )
    register_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )

    # ------------------------------------------------------------------
    # list
    # ------------------------------------------------------------------
    list_parser = subparsers.add_parser(
        "list",
        help="List agents in the repository",
    )
    list_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )
    list_parser.add_argument("--name", type=str, default=None, help="Filter by exact name")
    list_parser.add_argument(
        "--agent-type",
        type=str,
        default=None,
        help="Filter by agent type (task, domain, planner, etc.)",
    )
    list_parser.add_argument("--tag", type=str, default=None, help="Filter by tag")
    list_parser.add_argument("--owner", type=str, default=None, help="Filter by owner")

    # ------------------------------------------------------------------
    # show
    # ------------------------------------------------------------------
    show_parser = subparsers.add_parser(
        "show",
        help="Show full details for a single agent (by id or exact name)",
    )
    show_parser.add_argument(
        "identifier",
        type=str,
        help="Agent id (UUID) or exact name",
    )
    show_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )

    # ------------------------------------------------------------------
    # validate
    # ------------------------------------------------------------------
    validate_parser = subparsers.add_parser(
        "validate",
        help="Mark an agent as validated (optionally with a score)",
    )
    validate_parser.add_argument(
        "agent_id",
        type=str,
        help="Agent id (UUID)",
    )
    validate_parser.add_argument(
        "--score",
        type=float,
        default=None,
        help="Optional validation score",
    )
    validate_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )

    # ------------------------------------------------------------------
    # run-local
    # ------------------------------------------------------------------
    run_parser = subparsers.add_parser(
        "run-local",
        help="Run an agent implementation locally based on its registry spec",
    )
    run_parser.add_argument(
        "identifier",
        type=str,
        help="Agent id (UUID) or exact name",
    )
    run_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )
    run_parser.add_argument(
        "--inputs",
        type=str,
        default=None,
        help="Path to a JSON file containing inputs for the agent run",
    )
    run_parser.add_argument(
        "--workdir",
        type=str,
        default=str(Path.home() / ".academy" / "agents"),
        help="Directory in which to clone/cache agent repos",
    )
    run_parser.add_argument(
        "--target",
        type=str,
        default="local",
        help="Logical deployment target name to record (default: local)",
    )

    # ------------------------------------------------------------------
    # deploy
    # ------------------------------------------------------------------
    deploy_parser = subparsers.add_parser(
        "deploy",
        help="Create a stub deployment record for an agent",
    )
    deploy_parser.add_argument(
        "agent_id",
        type=str,
        help="Agent id (UUID)",
    )
    deploy_parser.add_argument(
        "--target",
        type=str,
        default="dev",
        help="Logical deployment target (default: dev)",
    )
    deploy_parser.add_argument(
        "--base-url",
        type=str,
        default="http://localhost:8000",
        help="Base URL of the Agent Repository backend (default: http://localhost:8000)",
    )


    # ------------------------------------------------------------------
    # init
    # ------------------------------------------------------------------
    init_parser = subparsers.add_parser(
        "init",
        help="Create a commented template agent.yaml file",
    )
    init_parser.add_argument(
        "path",
        type=str,
        nargs="?",
        default="agent.yaml",
        help="Path to write the template agent.yaml (default: agent.yaml)",
    )

    args = parser.parse_args(argv)

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------
    if args.command == "register":
        path = Path(args.path)
        payload = _load_yaml(path)
        client = AgentClient(base_url=args.base_url)
        created = client.create_agent(payload)
        print(created.get("id", ""))
        return 0

    if args.command == "list":
        client = AgentClient(base_url=args.base_url)
        agents = client.list_agents(
            name=args.name,
            agent_type=args.agent_type,
            tag=args.tag,
            owner=args.owner,
        )
        _print_agent_list(agents)
        return 0

    if args.command == "run-local":
        cfg = LocalRunConfig(
            base_url=args.base_url,
            workdir=Path(args.workdir),
            inputs_path=Path(args.inputs) if args.inputs else None,
            target=args.target,
        )
        result = run_local(args.identifier, cfg)
        # Print result as JSON
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "show":
        client = AgentClient(base_url=args.base_url)
        ident = args.identifier
        # Heuristic: if it looks like a UUID, treat it as id; otherwise use name.
        # (You can refine this if needed.)
        agent: Dict[str, Any]
        if len(ident) == 36 and ident.count("-") == 4:
            agent = client.get_agent(ident)
        else:
            agent = client.find_agent_by_name(ident)
        _print_agent_detail(agent)
        return 0

    if args.command == "validate":
        client = AgentClient(base_url=args.base_url)
        updated = client.validate_agent(args.agent_id, score=args.score)
        _print_agent_detail(updated)
        return 0

    if args.command == "init":
        path = Path(args.path)
        _write_template_yaml(path)
        print(f"Wrote template agent spec to {path}")
        return 0

    if args.command == "deploy":
        client = AgentClient(base_url=args.base_url)
        dep = client.deploy_agent(args.agent_id, target=args.target)
        _print_agent_detail(dep)
        return 0


    # Should not reach here because of required=True on subparsers
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())


