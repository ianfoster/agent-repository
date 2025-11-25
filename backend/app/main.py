from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from .schemas import (
    AgentSpec,
    AgentCreate,
    Deployment,
    DeploymentCreate,
    RunRequest,
    RunResult,
)
from .runner import stage_agent_code, run_agent_locally_from_staged
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


@app.post("/agents/{agent_id}/validate", response_model=AgentSpec)
def validate_agent(
    agent_id: UUID,
    score: Optional[float] = Query(default=None, description="Optional validation score"),
    db: Session = Depends(get_db),
) -> AgentSpec:
    """
    Mark an agent as validated and optionally set a validation score.
    """
    validated = crud.validate_agent(db, str(agent_id), score=score)
    if validated is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return validated


# ----------------------------------------------------------------------
# Deployment: stage code from GitHub into a local path
# ----------------------------------------------------------------------


@app.post("/agents/{agent_id}/deploy", response_model=Deployment, status_code=201)
def deploy_agent(
    agent_id: UUID,
    payload: DeploymentCreate,
    db: Session = Depends(get_db),
) -> Deployment:
    """
    Deploy (stage) an agent's code to a logical target.

    For local targets, this clones/updates the agent's git_repo into a
    deterministic directory under AGENTS_WORKDIR (or ~/.academy/agents),
    and records that path in the Deployment record with status='ready'.
    """
    agent = crud.get_agent(db, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    root = os.getenv("AGENTS_WORKDIR")
    workdir = Path(root) if root else Path.home() / ".academy" / "agents"

    try:
        staged_path = stage_agent_code(agent, workdir, payload.target)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Deployment failed: {e}") from e

    dep = crud.create_deployment(
        db,
        str(agent_id),
        payload,
        local_path=str(staged_path),
        status="ready",
    )
    if dep is None:
        raise HTTPException(status_code=500, detail="Failed to record deployment")
    return dep


@app.get("/agents/{agent_id}/deployments", response_model=List[Deployment])
def list_deployments(
    agent_id: UUID,
    db: Session = Depends(get_db),
) -> List[Deployment]:
    """
    List recent deployments for an agent.
    """
    return crud.list_deployments_for_agent(db, str(agent_id))


# ----------------------------------------------------------------------
# Run: execute previously staged code for a given target
# ----------------------------------------------------------------------


@app.post("/agents/{agent_id}/run", response_model=RunResult)
def run_agent(
    agent_id: UUID,
    payload: RunRequest,
    db: Session = Depends(get_db),
) -> RunResult:
    """
    Execute an agent implementation using an existing deployment.

    This endpoint:
      1. looks up a 'ready' Deployment for (agent_id, payload.target),
      2. runs the agent's entrypoint using the staged code at that deployment's path,
      3. returns the outputs together with the deployment metadata.

    If no suitable deployment exists, a 409 is returned with guidance to deploy first.
    """
    agent = crud.get_agent(db, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    dep = crud.get_latest_ready_deployment(db, str(agent_id), payload.target)
    if dep is None or not dep.local_path:
        raise HTTPException(
            status_code=409,
            detail=f"No ready deployment for target {payload.target!r}. Deploy this agent first.",
        )

    try:
        outputs = run_agent_locally_from_staged(agent, payload, Path(dep.local_path))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}") from e

    return RunResult(outputs=outputs, deployment=dep)
