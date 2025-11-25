from typing import Any, Dict, List, Optional
import httpx

class AgentClient:
    """
    Python SDK client for the Academy Agent Repository.

    Talks to:
      - GET  /health
      - GET  /agents
      - POST /agents
      - GET  /agents/{id}
      - POST /agents/{id}/validate
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Basic health
    # ------------------------------------------------------------------
    def health(self) -> Dict[str, Any]:
        resp = httpx.get(f"{self.base_url}/health", timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------
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

        resp = httpx.get(
            f"{self.base_url}/agents",
            params=params or None,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """
        Retrieve a single agent by ID.
        """
        resp = httpx.get(
            f"{self.base_url}/agents/{agent_id}",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def find_agent_by_name(self, name: str) -> Dict[str, Any]:
        """
        Find an agent by exact name.

        If multiple agents share the same name, this returns the first one.
        If none are found, raises a ValueError.
        """
        agents = self.list_agents(name=name)
        if not agents:
            raise ValueError(f"No agent found with name: {name}")
        if len(agents) > 1:
            # You can refine this heuristic later if needed.
            # For now, just return the first and document the behavior.
            # Or raise if you prefer strictness.
            # raise ValueError(f"Multiple agents found with name: {name}")
            return agents[0]
        return agents[0]

    def create_agent(self, agent_payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = httpx.post(
            f"{self.base_url}/agents",
            json=agent_payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def validate_agent(
        self,
        agent_id: str,
        score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Mark an agent as validated, optionally with a validation score.
        """
        params: Dict[str, Any] = {}
        if score is not None:
            params["score"] = score

        resp = httpx.post(
            f"{self.base_url}/agents/{agent_id}/validate",
            params=params or None,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def run_agent(
        self,
        agent_id: str,
        target: str,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Call the backend /agents/{id}/run endpoint.

        This executes the agent using an existing deployment for the given
        target and returns outputs + deployment metadata.
        """
        payload: Dict[str, Any] = {
            "target": target,
            "inputs": inputs or {},
        }
        resp = httpx.post(
            f"{self.base_url}/agents/{agent_id}/run",
            json=payload,
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    # ------------------------------------------------------------------
    # Deployments
    # ------------------------------------------------------------------
    def deploy_agent(self, agent_id: str, target: str) -> Dict[str, Any]:
        """
        Create a stub deployment record for an agent.
        """
        resp = httpx.post(
            f"{self.base_url}/agents/{agent_id}/deploy",
            json={"target": target},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def list_deployments(self, agent_id: str) -> List[Dict[str, Any]]:
        """
        List stub deployments for an agent.
        """
        resp = httpx.get(
            f"{self.base_url}/agents/{agent_id}/deployments",
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

