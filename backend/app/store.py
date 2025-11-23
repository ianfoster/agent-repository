from __future__ import annotations

from typing import Dict, List, Optional
from uuid import UUID

from .schemas import AgentSpec, AgentCreate


class InMemoryAgentStore:
    """
    Very simple in-memory store for agents.

    This is intentionally minimal and will later be replaced by a
    persistent backend (e.g., Postgres + SQLAlchemy).
    """

    def __init__(self) -> None:
        self._agents: Dict[UUID, AgentSpec] = {}

    def add(self, data: AgentCreate) -> AgentSpec:
        # 👇 THIS is the important part for Pydantic v2
        agent = AgentSpec(**data.model_dump())
        self._agents[agent.id] = agent
        return agent

    def get(self, agent_id: UUID) -> Optional[AgentSpec]:
        return self._agents.get(agent_id)

    def list(
        self,
        name: Optional[str] = None,
        agent_type: Optional[str] = None,
        tag: Optional[str] = None,
        owner: Optional[str] = None,
    ) -> List[AgentSpec]:
        agents = list(self._agents.values())

        if name is not None:
            agents = [a for a in agents if a.name == name]

        if agent_type is not None:
            agents = [a for a in agents if a.agent_type == agent_type]

        if tag is not None:
            agents = [a for a in agents if tag in a.tags]

        if owner is not None:
            agents = [a for a in agents if a.owner == owner]

        return agents

