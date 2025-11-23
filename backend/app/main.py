from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query

from .schemas import AgentSpec, AgentCreate
from .store import InMemoryAgentStore

app = FastAPI(
    title="Academy Agent Repository Backend",
    version="0.1.0",
    description="Core API for the Academy Agent Repository.",
)

store = InMemoryAgentStore()


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}


@app.post("/agents", response_model=AgentSpec, status_code=201)
def create_agent(payload: AgentCreate) -> AgentSpec:
    agent = store.add(payload)
    return agent


@app.get("/agents", response_model=List[AgentSpec])
def list_agents(
    name: Optional[str] = Query(default=None),
    agent_type: Optional[str] = Query(default=None),
    tag: Optional[str] = Query(default=None),
    owner: Optional[str] = Query(default=None),
) -> List[AgentSpec]:
    return store.list(name=name, agent_type=agent_type, tag=tag, owner=owner)


@app.get("/agents/{agent_id}", response_model=AgentSpec)
def get_agent(agent_id: UUID) -> AgentSpec:
    agent = store.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

