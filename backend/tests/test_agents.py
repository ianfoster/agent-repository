"""New tests for the current API and data model, including A2A Agent Cards."""

import os
from typing import Any, Dict

from fastapi.testclient import TestClient

from app.main import app

# During tests, we don't want to actually git-clone anything.
os.environ["AGENTS_SKIP_GIT"] = "1"

client = TestClient(app)


def _sample_agent_payload_v2() -> Dict[str, Any]:
    """Minimal sample payload for registering an agent."""
    return {
        "name": "materials-screening-agent",
        "version": "0.1.0",
        "description": "Demo materials screening agent.",
        "agent_type": "domain",
        "tags": ["materials", "screening"],
        "owner": "team-materials",
        "inputs": {
            "materials": {
                "description": "List of material identifiers",
                "type": "json",
                "required": True
            }
        },
        "outputs": {
            "results": {
                "description": "List of per-material scores and labels",
                "type": "json",
                "required": True
            }
        },
        "a2a_card": {
            "name": "materials-screening-agent",
            "url": "https://github.com/ianfoster/agent-repository/tree/main/examples/materials-screening-agent",
            "description": "Demo materials screening agent that returns a stability score and qualitative label for each material.",
            "version": "0.1.0",
            "protocolVersion": "0.2.6",
            "capabilities": {},
            "skills": [],
            "defaultInputModes": ["application/json"],
            "defaultOutputModes": ["application/json"],
            "supportsAuthenticatedExtendedCard": False
        },
        "git_repo": "https://github.com/ianfoster/agent-repository",
        "git_commit": "",
        "container_image": "",
        "entrypoint": "agents_demo.materials_screening:MaterialsScreeningAgent"
    }


def test_register_agent_roundtrip():
    payload = _sample_agent_payload_v2()

    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()

    assert "id" in created
    assert created["name"] == payload["name"]
    assert created["version"] == payload["version"]
    assert created["agent_type"] == payload["agent_type"]

    if "tags" in created:
        assert "materials" in created["tags"]

    if "a2a_card" in created:
        assert created["a2a_card"]["name"] == payload["a2a_card"]["name"]
        assert created["a2a_card"]["version"] == payload["a2a_card"]["version"]


def test_get_agent_by_id():
    payload = _sample_agent_payload_v2()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    agent_id = created["id"]

    resp2 = client.get(f"/agents/{agent_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()

    assert fetched["id"] == agent_id
    assert fetched["name"] == payload["name"]
    assert fetched["version"] == payload["version"]

    if "a2a_card" in fetched:
        assert fetched["a2a_card"]["name"] == payload["a2a_card"]["name"]
        assert fetched["a2a_card"]["version"] == payload["a2a_card"]["version"]


def test_list_agents_contains_registered():
    a1 = _sample_agent_payload_v2()
    a1["name"] = "materials-screening-agent"
    resp1 = client.post("/agents", json=a1)
    assert resp1.status_code == 201
    created1 = resp1.json()

    a2 = _sample_agent_payload_v2()
    a2["name"] = "stats-demo-agent"
    a2["description"] = "Demo stats agent."
    resp2 = client.post("/agents", json=a2)
    assert resp2.status_code == 201
    created2 = resp2.json()

    resp_all = client.get("/agents")
    assert resp_all.status_code == 200
    all_agents = resp_all.json()

    ids = {a["id"] for a in all_agents}
    assert created1["id"] in ids
    assert created2["id"] in ids


def test_validate_agent_marks_as_validated():
    payload = _sample_agent_payload_v2()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    agent_id = created["id"]

    resp_val = client.post(f"/agents/{agent_id}/validate")
    assert resp_val.status_code == 200
    validated = resp_val.json()

    assert validated.get("validation_status") == "validated"
    assert validated.get("last_validated_at") is not None

    resp2 = client.get(f"/agents/{agent_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched.get("validation_status") == "validated"
    assert fetched.get("last_validated_at") is not None
