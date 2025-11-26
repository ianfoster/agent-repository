# backend/tests/test_smoke.py

from fastapi.testclient import TestClient

from app.main import app  # adjust import if your app is elsewhere


client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("service") == "backend"


def test_agents_endpoint_exists():
    # Just check that /agents endpoint exists and returns JSON.
    resp = client.get("/agents")
    # Depending on your implementation, this might be 200 with an empty list,
    # or 200 with some agents, or 404 if no route. Adjust as needed.
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
