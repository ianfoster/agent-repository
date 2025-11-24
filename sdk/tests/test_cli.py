from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import pytest

from academy_agents.cli import main as cli_main


class DummyClient:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
        self.base_url = base_url
        self.timeout = timeout
        self.last_payload: Dict[str, Any] | None = None

    def create_agent(self, agent_payload: Dict[str, Any]) -> Dict[str, Any]:
        self.last_payload = agent_payload
        # Simulate backend adding an id
        result = dict(agent_payload)
        result["id"] = "dummy-id-123"
        return result


def test_cli_register_reads_yaml_and_calls_client(monkeypatch, tmp_path: Path, capsys):
    # Prepare a minimal YAML agent spec
    agent_yaml = tmp_path / "agent.yaml"
    agent_yaml.write_text(
        """
name: cli-test-agent
version: "0.1.0"
description: Agent registered via CLI
agent_type: task
tags: ["cli", "test"]
inputs: {}
outputs: {}
owner: cli-tests
git_repo: https://github.com/example/cli-agent
        """,
        encoding="utf-8",
    )

    dummy_client = DummyClient(base_url="http://example.org")

    def fake_client_init(base_url: str = "http://localhost:8000", timeout: float = 5.0):
        # ignore args, return our dummy
        return dummy_client

    # Patch AgentClient constructor used in cli
    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    # Run CLI main with custom argv
    exit_code = cli_main(["register", str(agent_yaml), "--base-url", "http://example.org"])
    assert exit_code == 0

    # Ensure client was called with YAML contents
    assert dummy_client.last_payload is not None
    assert dummy_client.last_payload["name"] == "cli-test-agent"
    assert dummy_client.last_payload["git_repo"] == "https://github.com/example/cli-agent"

    # Check that CLI printed an id
    captured = capsys.readouterr()
    assert "dummy-id-123" in captured.out


def test_cli_register_missing_file(tmp_path: Path):
    # Call CLI with a non-existent file path
    missing = tmp_path / "missing.yaml"
    # We expect the CLI helper to raise FileNotFoundError in this case
    with pytest.raises(FileNotFoundError):
        cli_main(["register", str(missing)])

