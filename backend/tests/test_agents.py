from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use a separate SQLite DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_agents.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

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
        "owner": "team-materials",
        "a2a_card": {
            "name": "materials-screening-agent",
            "url": "http://localhost:8000/a2a/materials-screening-agent",
            "description": "A2A-compatible materials screening agent.",
            "version": "1.0.0",
            "protocolVersion": "0.2.6",
            "capabilities": {},
            "skills": [],
            "defaultInputModes": ["text/plain"],
            "defaultOutputModes": ["text/plain"],
            "supportsAuthenticatedExtendedCard": False
        },
        "git_repo": "https://github.com/example/materials-agent",
        "git_commit": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
        "container_image": "ghcr.io/example/materials-agent:1.0.0",
        "entrypoint": "agents.materials:MaterialsScreeningAgent"
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

    # A2A card round-trip
    assert data["a2a_card"]["name"] == payload["a2a_card"]["name"]
    assert data["a2a_card"]["url"] == payload["a2a_card"]["url"]

    # GitHub / container metadata round-trip
    assert data["git_repo"] == payload["git_repo"]
    assert data["git_commit"] == payload["git_commit"]
    assert data["container_image"] == payload["container_image"]
    assert data["entrypoint"] == payload["entrypoint"]

    # Validation defaults
    assert data["validation_status"] == "unvalidated"
    assert data["last_validated_at"] is None
    assert data["validation_score"] is None



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
    assert fetched["a2a_card"]["version"] == payload["a2a_card"]["version"]
    assert fetched["git_repo"] == payload["git_repo"]


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
    a2["a2a_card"]["name"] = "simulation-setup-agent"
    a2["git_repo"] = "https://github.com/example/sim-agent"
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


def test_validate_agent_updates_status_and_score():
    payload = _sample_agent_payload()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    agent_id = created["id"]

    # Initially unvalidated
    assert created["validation_status"] == "unvalidated"
    assert created["last_validated_at"] is None
    assert created["validation_score"] is None

    # Validate with a score
    resp2 = client.post(f"/agents/{agent_id}/validate", params={"score": 0.9})
    assert resp2.status_code == 200
    validated = resp2.json()

    assert validated["validation_status"] == "validated"
    assert validated["validation_score"] == 0.9
    assert validated["last_validated_at"] is not None

def test_deploy_agent_creates_deployment():
    payload = _sample_agent_payload()
    resp = client.post("/agents", json=payload)
    assert resp.status_code == 201
    created = resp.json()
    agent_id = created["id"]

    # Deploy to target "dev"
    resp_dep = client.post(f"/agents/{agent_id}/deploy", json={"target": "dev"})
    assert resp_dep.status_code == 201
    dep = resp_dep.json()
    assert dep["agent_id"] == agent_id
    assert dep["target"] == "dev"
    assert dep["status"] == "requested"

    # List deployments
    resp_list = client.get(f"/agents/{agent_id}/deployments")
    assert resp_list.status_code == 200
    deps = resp_list.json()
    assert len(deps) >= 1
    assert deps[0]["agent_id"] == agent_id

