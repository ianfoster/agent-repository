from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict

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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="academy-agents",
        description="CLI for interacting with the Academy Agent Repository",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `academy-agents register agent.yaml --base-url http://...`
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

    args = parser.parse_args(argv)

    if args.command == "register":
        path = Path(args.path)
        payload = _load_yaml(path)
        client = AgentClient(base_url=args.base_url)
        created = client.create_agent(payload)
        # Print the id to stdout for scripting
        print(created.get("id", ""))
        return 0

    # Should not reach here because of required=True on subparsers
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

