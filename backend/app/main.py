# backend/app/main.py
from __future__ import annotations

from .academy_runtime import start_academy_instance
from .schemas import StartInstanceRequest, InstanceResponse
from .models import AgentImplementation

import os
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from .database import engine, get_db
from .models import Base, AgentImplementation, Location as LocationModel
from . import crud
from .schemas import (
    AgentCard,
    AgentCardCreate,
    Location,
    LocationCreate,
    Deployment,
    DeploymentCreate,
    RunRequest,
    RunResult,
)
from .runtime import stage_agent_code, run_agent_locally_from_staged

app = FastAPI(
    title="Academy Agent Repository",
    version="0.1.0",
    description="Registry and control plane for Academy-based agents.",
)

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "service": "backend"}


# -------- Agents --------

@app.post("/agents", response_model=AgentCard, status_code=201)
def register_agent(card_in: AgentCardCreate, db: Session = Depends(get_db)) -> AgentCard:
    # For now: always create; you could implement upsert by (name, version)
    return crud.create_agent(db, card_in)


@app.get("/agents", response_model=List[AgentCard])
def list_agents(db: Session = Depends(get_db)) -> List[AgentCard]:
    return crud.list_agents(db)


@app.get("/agents/{agent_id}", response_model=AgentCard)
def get_agent(agent_id: UUID, db: Session = Depends(get_db)) -> AgentCard:
    card = crud.get_agent(db, str(agent_id))
    if card is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return card


@app.post("/agents/{agent_id}/validate", response_model=AgentCard)
def validate_agent(
    agent_id: UUID,
    score: Optional[float] = Query(default=None),
    db: Session = Depends(get_db),
) -> AgentCard:
    agent = db.get(AgentImplementation, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Stage (and optionally run) as simple validation
    root = os.getenv("AGENTS_WORKDIR")
    workdir = Path(root) if root else Path.home() / ".academy" / "agents"

    # for validation, treat location logically as "local-validate"
    # (or look up a corresponding LocationModel if you want)
    dummy_loc = LocationModel(id="local-validate", name="local-validate", location_type="local", config={})

    try:
        staged_path = stage_agent_code(agent, dummy_loc, workdir)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Validation failed during staging: {e}"
        ) from e

    # Optional smoke run
    if agent.validation_inputs:
        req = RunRequest(inputs=agent.validation_inputs, target="local-validate")
        try:
            _ = run_agent_locally_from_staged(agent, req, staged_path)
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Validation failed during test run: {e}"
            ) from e

    card = crud.mark_agent_validated(db, str(agent_id), score=score)
    if card is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return card


# -------- Locations --------

@app.post("/locations", response_model=Location, status_code=201)
def register_location(loc_in: LocationCreate, db: Session = Depends(get_db)) -> Location:
    return crud.create_location(db, loc_in)


@app.get("/locations", response_model=List[Location])
def list_locations(db: Session = Depends(get_db)) -> List[Location]:
    return crud.list_locations(db)


# -------- Deployments --------

@app.post("/deployments", response_model=Deployment, status_code=201)
def deploy_agent(
    dep_in: DeploymentCreate,
    db: Session = Depends(get_db),
) -> Deployment:
    agent = db.get(AgentImplementation, str(dep_in.agent_id))
    loc = db.get(LocationModel, str(dep_in.location_id))
    if agent is None or loc is None:
        raise HTTPException(status_code=404, detail="Agent or Location not found")

    root = os.getenv("AGENTS_WORKDIR")
    workdir = Path(root) if root else Path.home() / ".academy" / "agents"

    try:
        staged_path = stage_agent_code(agent, loc, workdir)
    except Exception as e:
        # record failure
        dep = crud.create_deployment(
            db, dep_in, local_path=None, status="failed", metadata={"error": str(e)}
        )
        raise HTTPException(
            status_code=500, detail=f"Deployment failed during staging: {e}"
        ) from e

    dep = crud.create_deployment(
        db,
        dep_in,
        local_path=str(staged_path),
        status="ready",
        metadata={"note": "staged successfully"},
    )
    if dep is None:
        raise HTTPException(status_code=500, detail="Failed to record deployment")
    return dep


@app.get("/agents/{agent_id}/deployments", response_model=List[Deployment])
def list_deployments_for_agent(
    agent_id: UUID, db: Session = Depends(get_db)
) -> List[Deployment]:
    return crud.list_deployments_for_agent(db, str(agent_id))


# -------- Run (one-off) --------

@app.post("/agents/{agent_id}/run", response_model=RunResult)
def run_agent(
    agent_id: UUID,
    req: RunRequest,
    db: Session = Depends(get_db),
) -> RunResult:
    agent = db.get(AgentImplementation, str(agent_id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Find appropriate location
    if req.target:
        loc = crud.find_location_by_name(db, req.target) or None
        if loc is None:
            raise HTTPException(
                status_code=404,
                detail=f"Location {req.target!r} not found",
            )
    else:
        raise HTTPException(status_code=400, detail="target is required")

    dep = crud.get_latest_ready_deployment(db, str(agent_id), loc.id)
    if dep is None or not dep.local_path:
        raise HTTPException(
            status_code=409,
            detail=f"No ready deployment for agent {agent_id} on location {loc.name!r}",
        )

    outputs = run_agent_locally_from_staged(
        agent, req, Path(dep.local_path)
    )

    return RunResult(outputs=outputs, deployment=dep)

@app.post("/instances", response_model=InstanceResponse)
async def start_instance(
    req: StartInstanceRequest,
    db: Session = Depends(get_db),
):
    agent = db.get(AgentImplementation, str(req.agent_id))
    if agent is None:
        raise HTTPException(404, "Agent not found")

    loc = crud.find_location_by_name(db, req.location_name)
    if loc is None:
        raise HTTPException(404, "Location not found")

    # Optionally require a ready deployment here; for now, ignore.
    outputs, handle = await start_academy_instance(agent, loc, req.init_inputs or {})

    # You decide how to serialize handle (could be repr(handle), handle.agent_id, etc.)
    inst = crud.create_instance(db, deployment_id="some-dep-id", handle=str(handle), endpoint=None)
    return inst


@app.post("/agents/{agent_id}/instances", response_model=InstanceResponse)
async def start_agent_instance(
    agent_id: UUID,
    req: StartInstanceRequest,
    db: Session = Depends(get_db),
) -> InstanceResponse:
    """
    Start a running Academy-based agent instance from a registered implementation.

    For now, this uses a single local Manager (thread-based) and stores handles
    in memory only (no DB persistence).
    """
    agent_impl = db.get(AgentImplementation, str(agent_id))
    if agent_impl is None:
        raise HTTPException(status_code=404, detail="Agent not found")

    try:
        instance_id = await start_academy_instance(agent_impl)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start instance: {e}") from e

    return InstanceResponse(
        instance_id=instance_id,
        agent_id=str(agent_id),
        status="running",
    )
