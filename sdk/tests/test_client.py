import pytest
from typing import Any, Dict, List

from academy_agents import AgentClient


def test_client_init():
    client = AgentClient(base_url="http://example.org", timeout=10.0)
    assert client.base_url == "http://example.org"
    assert client.timeout == 10.0


def test_list_agents_uses_httpx_get(monkeypatch):
    called: Dict[str, Any] = {}

    def fake_get(url: str, params: Dict[str, Any] | None, timeout: float):
        called["url"] = url
        called["params"] = params
        called["timeout"] = timeout

        class FakeResponse:
            status_code = 200

            def raise_for_status(self) -> None:
                return None

            def json(self) -> List[Dict[str, Any]]:
                return [
                    {"id": "123", "name": "test-agent", "agent_type": "task"}
                ]

        return FakeResponse()

    # Patch the httpx.get function used in the client module
    monkeypatch.setattr("academy_agents.client.httpx.get", fake_get)

    client = AgentClient(base_url="http://example.org", timeout=3.0)
    agents = client.list_agents(agent_type="task")
    assert len(agents) == 1
    assert agents[0]["name"] == "test-agent"

    assert called["url"] == "http://example.org/agents"
    assert called["params"]["agent_type"] == "task"
    assert called["timeout"] == 3.0


def test_create_agent_uses_httpx_post(monkeypatch):
    called: Dict[str, Any] = {}

    def fake_post(url: str, json: Dict[str, Any], timeout: float):
        called["url"] = url
        called["json"] = json
        called["timeout"] = timeout

        class FakeResponse:
            status_code = 201

            def raise_for_status(self) -> None:
                return None

            def json(self) -> Dict[str, Any]:
                # Echo back as if backend created an id
                result = dict(json)
                result["id"] = "abc-123"
                return result

        return FakeResponse()

    monkeypatch.setattr("academy_agents.client.httpx.post", fake_post)

    client = AgentClient(base_url="http://example.org", timeout=4.0)
    payload = {
        "name": "sdk-test-agent",
        "version": "0.1.0",
        "description": "Created via SDK",
        "agent_type": "task",
        "tags": [],
        "inputs": {},
        "outputs": {},
        "owner": "sdk-tests"
    }
    created = client.create_agent(payload)

    assert created["id"] == "abc-123"
    assert created["name"] == "sdk-test-agent"
    assert called["url"] == "http://example.org/agents"
    assert called["json"]["name"] == "sdk-test-agent"
    assert called["timeout"] == 4.0


@pytest.mark.skip(reason="Requires running backend at localhost:8000")
def test_client_health_live():
    client = AgentClient()
    data = client.health()
    assert data["status"] == "ok"

