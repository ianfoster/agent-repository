# sdk/academy_agents/client.py
from __future__ import annotations

from typing import Any, Dict, List, Optional
import httpx


class AgentClient:
    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 10.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # -------- basic helpers --------

    def _get(self, path: str) -> httpx.Response:
        return httpx.get(f"{self.base_url}{path}", timeout=self.timeout)

    def _post(self, path: str, json: Optional[Dict[str, Any]] = None) -> httpx.Response:
        return httpx.post(f"{self.base_url}{path}", json=json, timeout=self.timeout)

    # -------- health --------

    def health(self) -> Dict[str, Any]:
        r = self._get("/health")
        r.raise_for_status()
        return r.json()

    # -------- agents --------

    # duplicate of create_agent?
    def register_agent(self, card: Dict[str, Any]) -> Dict[str, Any]:
        r = self._post("/agents", json=card)
        r.raise_for_status()
        return r.json()

    def create_agent(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create (register) a new agent implementation.

        This is used by the CLI's `academy-agents register` command.
        """
        resp = httpx.post(
            f"{self.base_url}/agents",
            json=card,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def list_agents(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        tag: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List agents, optionally filtering by name, type, tag, or owner.

        These parameters will be sent as query parameters to /agents.
        """
        params: Dict[str, Any] = {}
        if name is not None:
            params["name"] = name
        if agent_type is not None:
            params["agent_type"] = agent_type
        if tag is not None:
            params["tag"] = tag
        if owner is not None:
            params["owner"] = owner

        r = httpx.get(
            f"{self.base_url}/agents",
            params=params or None,
            timeout=self.timeout,
        )
        r.raise_for_status()
        return r.json()

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        r = self._get(f"/agents/{agent_id}")
        r.raise_for_status()
        return r.json()

    def find_agent_by_name_version(self, name: str, version: str = "0.1.0") -> Dict[str, Any]:
        agents = self.list_agents()
        for a in agents:
            if a["name"] == name and a["version"] == version:
                return a
        raise ValueError(f"No agent found with name={name!r}, version={version!r}")

    def validate_agent(self, agent_id: str, score: Optional[float] = None) -> Dict[str, Any]:
        params = {}
        if score is not None:
            params["score"] = score
        r = httpx.post(f"{self.base_url}/agents/{agent_id}/validate", params=params, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    # -------- locations --------

    def register_location(self, loc: Dict[str, Any]) -> Dict[str, Any]:
        r = self._post("/locations", json=loc)
        r.raise_for_status()
        return r.json()

    def list_locations(self) -> List[Dict[str, Any]]:
        r = self._get("/locations")
        r.raise_for_status()
        return r.json()

    # -------- deployments --------

    def deploy(self, agent_id: str, location_id: str) -> Dict[str, Any]:
        payload = {"agent_id": agent_id, "location_id": location_id}
        r = self._post("/deployments", json=payload)
        r.raise_for_status()
        return r.json()

    def list_deployments_for_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        r = self._get(f"/agents/{agent_id}/deployments")
        r.raise_for_status()
        return r.json()

    # -------- run --------

    def run_agent(
        self,
        agent_id: str,
        target: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {"target": target, "inputs": inputs or {}}
        r = self._post(f"/agents/{agent_id}/run", json=payload)
        r.raise_for_status()
        return r.json()
