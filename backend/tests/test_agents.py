from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def _sample_agent_payload() -> Dict[str, Any]:
    return {
        "name": "materials-screening-agent",
        "version": "1.0.0",
        "description": "Screens candidate materials for a target property.",
        "agent_type": "domain",
        "tags": ["materials", "screening"],
        "inputs": {
            "composition": {
                "description": "Material composition identifier",
                "type": "string",
                "required": True
            },
            "conditions": {
                "description": "Processing or environmental conditions",
                "type": "json",
                "required": False
            }
        },
        "outputs": {
            "predicted_property": {
                "description": "Predicted value of the target property",
                "type": "float",
                "required": True
            }
        },
        "owner": "team-materials"
    }


def test_create_agent():
    payload = _sample_agent_payload()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["id"]
    assert data["name"] == payload["name"]
    assert data["version"] == payload["version"]
    assert data["agent_type"] == payload["agent_type"]
    assert data["inputs"]["composition"]["description"] == payload["inputs"]["composition"]["description"]
    assert "created_at" in data


def test_get_agent_by_id():
    payload = _sample_agent_payload()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    agent_id = created["id"]

    resp2 = client.get(f"/agents/{agent_id}")
    assert resp2.status_code == 200
    fetched = resp2.json()
    assert fetched["id"] == agent_id
    assert fetched["name"] == payload["name"]


def test_list_agents_and_filter():
    a1 = _sample_agent_payload()
    a1["tags"] = ["materials", "screening"]
    a1["owner"] = "team-materials"
    resp1 = client.post("/agents", json=a1)
    assert resp1.status_code == 201

    a2 = _sample_agent_payload()
    a2["name"] = "simulation-setup-agent"
    a2["tags"] = ["simulation"]
    a2["owner"] = "team-sim"
    resp2 = client.post("/agents", json=a2)
    assert resp2.status_code == 201

    resp_all = client.get("/agents")
    assert resp_all.status_code == 200
    all_agents = resp_all.json()
    assert len(all_agents) >= 2

    resp_mat = client.get("/agents", params={"tag": "materials"})
    assert resp_mat.status_code == 200
    mat_agents = resp_mat.json()
    assert all("materials" in a["tags"] for a in mat_agents)

    resp_owner = client.get("/agents", params={"owner": "team-sim"})
    assert resp_owner.status_code == 200
    owner_agents = resp_owner.json()
    assert all(a["owner"] == "team-sim" for a in owner_agents)


def test_get_agent_not_found():
    resp = client.get("/agents/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Agent not found"

