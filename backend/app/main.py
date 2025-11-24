from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from .schemas import AgentSpec, AgentCreate, Deployment, DeploymentCreate, RunRequest, RunResult
from .runner import run_agent_locally
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
# Deployment stubs
# ----------------------------------------------------------------------


@app.post("/agents/{agent_id}/deploy", response_model=Deployment, status_code=201)
def deploy_agent(
    agent_id: UUID,
    payload: DeploymentCreate,
    db: Session = Depends(get_db),
) -> Deployment:
    """
    Create a stub deployment record for an agent.

    This does not actually run anything; it simply records that an agent
    was asked to be deployed to a given target.
    """
    dep = crud.create_deployment(db, str(agent_id), payload)
    if dep is None:
        raise HTTPException(status_code=404, detail="Agent not found")
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


@app.post("/agents/{agent_id}/run", response_model=RunResult)
def run_agent(
    agent_id: UUID,
    payload: RunRequest,
    db: Session = Depends(get_db),
) -> RunResult:
    """
    Execute an agent implementation locally on the backend host.

    This:
      1. fetches the agent spec
      2. clones/updates git_repo
      3. imports the entrypoint
      4. calls run(**inputs)
      5. records a stub Deployment with the requested target
      6. returns outputs + deployment
    """
    agent = crud.get_agent(db, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        outputs = run_agent_locally(agent, payload)
    except Exception as e:
        # You might want more structured error handling/logging later
        raise HTTPException(status_code=500, detail=f"Agent run failed: {e}") from e

    # Record a deployment stub
    dep = crud.create_deployment(
        db,
        str(agent_id),
        DeploymentCreate(target=payload.target),
    )

    return RunResult(outputs=outputs, deployment=dep)
