from typing import Any, Dict, List, Optional
import httpx


class AgentClient:
    """
    Minimal SDK client for the Academy Agent Repository.

    Talks to `/health` and `/agents`.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def health(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def list_agents(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        tag: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if agent_type is not None:
            params["agent_type"] = agent_type
        if tag is not None:
            params["tag"] = tag
        if owner is not None:
            params["owner"] = owner

        resp = httpx.get(f"{self.base_url}/agents", params=params or None, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def create_agent(self, agent_payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(f"{self.base_url}/agents", json=agent_payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

