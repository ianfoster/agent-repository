import pytest
from academy_agents import AgentClient

def test_client_init():
    c = AgentClient(base_url="http://example.org")
    assert c.base_url == "http://example.org"

@pytest.mark.skip(reason="Requires running backend")
def test_live():
    c = AgentClient()
    assert c.health()["status"] == "ok"
