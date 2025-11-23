from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from .schemas import AgentSpec, AgentCreate
from .database import Base, engine, get_db
from . import crud

app = FastAPI(
    title="Academy Agent Repository Backend",
    version="0.1.0",
    description="Core API for the Academy Agent Repository.",
)

# For dev simplicity: create tables on startup if they do not exist.
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    """
    Simple health check endpoint used by SDK, frontend, and CI tests.
    """
    return {"status": "ok", "service": "backend"}


@app.post("/agents", response_model=AgentSpec, status_code=201)
def create_agent(payload: AgentCreate, db: Session = Depends(get_db)) -> AgentSpec:
    """
    Register a new agent in the persistent repository.
    """
    return crud.create_agent(db, payload)


@app.get("/agents", response_model=List[AgentSpec])
def list_agents(
    name: Optional[str] = Query(default=None, description="Filter by exact agent name"),
    agent_type: Optional[str] = Query(default=None, description="Filter by agent type"),
    tag: Optional[str] = Query(default=None, description="Filter by tag"),
    owner: Optional[str] = Query(default=None, description="Filter by owner"),
    db: Session = Depends(get_db),
) -> List[AgentSpec]:
    """
    List agents in the repository, with simple filtering support.
    """
    return crud.list_agents(
        db=db,
        name=name,
        agent_type=agent_type,
        tag=tag,
        owner=owner,
    )


@app.get("/agents/{agent_id}", response_model=AgentSpec)
def get_agent(agent_id: UUID, db: Session = Depends(get_db)) -> AgentSpec:
    """
    Retrieve a single agent by its UUID.
    """
    agent = crud.get_agent(db, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent

