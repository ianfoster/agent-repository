import httpx

class AgentClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    def health(self):
        resp = httpx.get(f"{self.base_url}/health", timeout=5.0)
        resp.raise_for_status()
        return resp.json()

    def list_agents(self):
        raise NotImplementedError("list_agents will be implemented later")
