from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from academy_agents.cli import main as cli_main


class DummyClient:
  def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
      self.base_url = base_url
      self.timeout = timeout
      self.last_payload: Dict[str, Any] | None = None
      self.list_return: List[Dict[str, Any]] = []
      self.get_return: Dict[str, Any] | None = None
      self.find_return: Dict[str, Any] | None = None
      self.validate_return: Dict[str, Any] | None = None

  def create_agent(self, agent_payload: Dict[str, Any]) -> Dict[str, Any]:
      self.last_payload = agent_payload
      result = dict(agent_payload)
      result["id"] = "dummy-id-123"
      return result

  def list_agents(self, **kwargs: Any) -> List[Dict[str, Any]]:
      return list(self.list_return)

  def get_agent(self, agent_id: str) -> Dict[str, Any]:
      if self.get_return is None:
          raise RuntimeError("get_return not set")
      return self.get_return

  def find_agent_by_name(self, name: str) -> Dict[str, Any]:
      if self.find_return is None:
          raise RuntimeError("find_return not set")
      return self.find_return

  def validate_agent(self, agent_id: str, score: float | None = None) -> Dict[str, Any]:
      if self.validate_return is None:
          raise RuntimeError("validate_return not set")
      return self.validate_return


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
        return dummy_client

    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    exit_code = cli_main(["register", str(agent_yaml), "--base-url", "http://example.org"])
    assert exit_code == 0

    assert dummy_client.last_payload is not None
    assert dummy_client.last_payload["name"] == "cli-test-agent"
    assert dummy_client.last_payload["git_repo"] == "https://github.com/example/cli-agent"

    captured = capsys.readouterr()
    assert "dummy-id-123" in captured.out


def test_cli_register_missing_file(tmp_path: Path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError):
        cli_main(["register", str(missing)])


def test_cli_list_uses_client(monkeypatch, capsys):
    dummy_client = DummyClient()
    dummy_client.list_return = [
        {
            "id": "id-1",
            "name": "agent-one",
            "version": "0.1.0",
            "agent_type": "task",
            "owner": "team-a",
            "validation_status": "validated",
        },
        {
            "id": "id-2",
            "name": "agent-two",
            "version": "0.2.0",
            "agent_type": "domain",
            "owner": "team-b",
            "validation_status": "unvalidated",
        },
    ]

    def fake_client_init(base_url: str = "http://localhost:8000", timeout: float = 5.0):
        return dummy_client

    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    exit_code = cli_main(["list"])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "agent-one" in out
    assert "agent-two" in out
    assert "validated" in out
    assert "unvalidated" in out


def test_cli_show_by_id_uses_get_agent(monkeypatch, capsys):
    dummy_client = DummyClient()
    dummy_client.get_return = {
        "id": "00000000-0000-0000-0000-000000000000",
        "name": "agent-one",
        "version": "0.1.0",
        "agent_type": "task",
        "owner": "team-a",
    }

    def fake_client_init(base_url: str = "http://localhost:8000", timeout: float = 5.0):
        return dummy_client

    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    # UUID-like identifier -> should use get_agent
    exit_code = cli_main(["show", "00000000-0000-0000-0000-000000000000"])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "agent-one" in out
    assert "00000000-0000-0000-0000-000000000000" in out



def test_cli_show_by_name_uses_find_agent(monkeypatch, capsys):
    dummy_client = DummyClient()
    dummy_client.find_return = {
        "id": "id-2",
        "name": "agent-two",
        "version": "0.2.0",
        "agent_type": "domain",
        "owner": "team-b",
    }

    def fake_client_init(base_url: str = "http://localhost:8000", timeout: float = 5.0):
        return dummy_client

    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    exit_code = cli_main(["show", "agent-two"])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "agent-two" in out
    assert "id-2" in out


def test_cli_validate_calls_client(monkeypatch, capsys):
    dummy_client = DummyClient()
    dummy_client.validate_return = {
        "id": "id-3",
        "validation_status": "validated",
        "validation_score": 0.93,
    }

    def fake_client_init(base_url: str = "http://localhost:8000", timeout: float = 5.0):
        return dummy_client

    monkeypatch.setattr("academy_agents.cli.AgentClient", fake_client_init)

    exit_code = cli_main(["validate", "id-3", "--score", "0.93"])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "id-3" in out
    assert "validated" in out
    assert "0.93" in out


def test_cli_init_writes_template(tmp_path: Path):
    target = tmp_path / "agent.yaml"
    assert not target.exists()
    exit_code = cli_main(["init", str(target)])
    assert exit_code == 0
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert "Minimal agent specification" in text
    assert "name: example-agent" in text

