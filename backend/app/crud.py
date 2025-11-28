# backend/app/crud.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from typing import Optional
from sqlalchemy.orm import Session

from . import models
from .schemas import AgentCardCreate, AgentCard, LocationCreate, Location, DeploymentCreate, Instance



# ---------- Agent implementations ----------

def create_agent(db: Session, card_in: AgentCardCreate) -> AgentCard:
    db_obj = models.AgentImplementation(
        id=str(uuid4()),
        name=card_in.name,
        version=card_in.version,
        description=card_in.description,
        agent_type=card_in.agent_type,
        tags=card_in.tags,
        inputs_schema=card_in.inputs_schema,
        outputs_schema=card_in.outputs_schema,
        git_repo=card_in.git_repo,
        git_commit=card_in.git_commit,
        container_image=card_in.container_image,
        entrypoint=card_in.entrypoint,
        validation_inputs=card_in.validation_inputs,
        validation_status="unvalidated",
        validation_score=card_in.validation_score,
        last_validated_at=card_in.last_validated_at,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return AgentCard.model_validate(db_obj)


def delete_agent(db: Session, agent_id: str) -> bool:
    """
    Delete an agent implementation by its ID.

    Returns True if a row was deleted, False if not found.
    """
    obj = db.get(models.AgentImplementation, agent_id)
    if obj is None:
        return False

    # If you want to also delete deployments, you can either:
    # - rely on cascade delete in your ORM relationship, or
    # - manually delete deployments here before deleting the agent.
    # For now, just delete the agent row.
    db.delete(obj)
    db.commit()
    return True


def list_agents(db: Session) -> List[AgentCard]:
    objs = db.query(models.AgentImplementation).all()
    return [AgentCard.model_validate(o) for o in objs]


def get_agent(db: Session, agent_id: str) -> Optional[AgentCard]:
    obj = db.get(models.AgentImplementation, agent_id)
    if obj is None:
        return None
    return AgentCard.model_validate(obj)


def find_agent_by_name_version(
    db: Session, name: str, version: str
) -> Optional[AgentCard]:
    obj = (
        db.query(models.AgentImplementation)
        .filter(
            models.AgentImplementation.name == name,
            models.AgentImplementation.version == version,
        )
        .one_or_none()
    )
    return AgentCard.model_validate(obj) if obj else None


def mark_agent_validated(
    db: Session, agent_id: str, score: Optional[float] = None
) -> Optional[AgentCard]:
    obj = db.get(models.AgentImplementation, agent_id)
    if obj is None:
        return None
    obj.validation_status = "validated"
    obj.last_validated_at = datetime.utcnow()
    if score is not None:
        obj.validation_score = score
    db.commit()
    db.refresh(obj)
    return AgentCard.model_validate(obj)


# ---------- Locations ----------

def create_location(db: Session, loc_in: LocationCreate) -> Location:
    db_obj = models.Location(
        id=str(uuid4()),
        name=loc_in.name,
        location_type=loc_in.location_type,
        config=loc_in.config,
        is_active=loc_in.is_active,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return Location.model_validate(db_obj)


def delete_location(db: Session, location_id: str) -> bool:
    """
    Delete a location by its ID.

    Returns True if a row was deleted, False if not found.
    """
    obj = db.get(models.Location, location_id)
    if obj is None:
        return False

    # NOTE: if you want to enforce "no deployments must exist for this location"
    # you could check for that here before deleting.
    db.delete(obj)
    db.commit()
    return True

def list_locations(db: Session) -> List[Location]:
    objs = db.query(models.Location).all()
    return [Location.model_validate(o) for o in objs]


def get_location(db: Session, loc_id: str) -> Optional[Location]:
    obj = db.get(models.Location, loc_id)
    return Location.model_validate(obj) if obj else None


def find_location_by_name(db: Session, name: str) -> Optional[Location]:
    obj = (
        db.query(models.Location)
        .filter(models.Location.name == name)
        .one_or_none()
    )
    return Location.model_validate(obj) if obj else None


# ---------- Deployments ----------

from typing import Optional
from uuid import uuid4
from sqlalchemy.orm import Session

from . import models

def create_deployment(
    db: Session,
    dep_in,
    local_path: Optional[str] = None,
    status: str = "requested",
    metadata: Optional[dict] = None,
) -> Optional[models.Deployment]:
    """
    Create or update a deployment record for an agent on a location.

    Idempotent per (agent_id, location_id): if a non-deleted deployment
    already exists, update it instead of inserting a new row.
    """
    agent_id_str = str(dep_in.agent_id)
    location_id_str = str(dep_in.location_id)

    # Ensure agent and location exist
    agent = db.get(models.AgentImplementation, agent_id_str)
    loc = db.get(models.Location, location_id_str)
    if agent is None or loc is None:
        return None

    # See if there is an existing non-deleted deployment
    existing = (
        db.query(models.Deployment)
        .filter(
            models.Deployment.agent_id == agent_id_str,
            models.Deployment.location_id == location_id_str,
            models.Deployment.status != "deleted",
        )
        .order_by(models.Deployment.created_at.desc())
        .first()
    )

    if existing:
        if local_path is not None:
            existing.local_path = local_path
        existing.status = status
        if metadata:
            if existing.meta is None:
                existing.meta = metadata
            else:
                existing.meta.update(metadata)
        db.commit()
        db.refresh(existing)
        return existing

    # No existing deployment → create new
    db_dep = models.Deployment(
        id=str(uuid4()),
        agent_id=agent_id_str,
        location_id=location_id_str,
        status=status,
        local_path=local_path,
        meta=metadata or {},
    )
    db.add(db_dep)
    db.commit()
    db.refresh(db_dep)
    return db_dep

def list_deployments_for_agent(
    db: Session, agent_id: str
) -> List[Deployment]:
    objs = (
        db.query(models.Deployment)
        .filter(models.Deployment.agent_id == agent_id)
        .order_by(models.Deployment.created_at.desc())
        .all()
    )
    return objs


def delete_deployment(db: Session, deployment_id: str) -> bool:
    """
    Delete a deployment row by its ID.

    Returns True if a row was deleted, False if not found.
    """
    obj = db.get(models.Deployment, deployment_id)
    if obj is None:
        return False

    db.delete(obj)
    db.commit()
    return True


def get_latest_ready_deployment(
    db: Session, agent_id: str, location_id: str
) -> Optional[models.Deployment]:
    """
    Return the most recent 'ready' Deployment for a given agent and location.

    Implementation note:
    We deliberately load all deployments and filter in Python to avoid any
    confusion with ORM mappings / status values. This is fine for a small
    prototype and easy to reason about.
    """
    print("DEBUG get_latest_ready_deployment:", agent_id, location_id)

    rows = db.query(models.Deployment).all()
    print("DEBUG get_latest_ready_deployment: all rows:")
    for r in rows:
        print("  ROW:", r.id, r.agent_id, r.location_id, repr(r.status))
        print("  TYPES:", type(r.id), type(r.agent_id), type(r.location_id), type(location_id), type(r.status))

    candidates = [
        r
        for r in rows
        if r.agent_id == agent_id
        and r.location_id == str(location_id)
        and r.status == "ready"
    ]

    # Sort newest first by created_at
    candidates.sort(key=lambda r: r.created_at, reverse=True)

    if not candidates:
        print("DEBUG get_latest_ready_deployment: no candidates found")
        return None

    chosen = candidates[0]
    print("DEBUG get_latest_ready_deployment: chosen:", chosen.id, chosen.local_path)
    return chosen

def get_latest_ready_deployment_old(
    db: Session, agent_id: str, location_id: str
) -> Optional[Deployment]:
    print("DEBUG get_latest_ready_deployment:", agent_id, location_id)
    q = (
        db.query(models.Deployment)
        .filter(
            models.Deployment.agent_id == agent_id,
            models.Deployment.location_id == location_id,
            models.Deployment.status == "ready",
        )
        .order_by(models.Deployment.created_at.desc())
    )
    obj = q.first()
    print("DEBUG get_latest_ready_deployment -> obj:", obj)
    #return Deployment.model_validate(obj) if obj else None
    #MOD
    return obj


# ---------- Instances (running agents) ----------

def create_instance(
    db: Session, deployment_id: str, handle: Optional[str], endpoint: Optional[str]
) -> Instance:
    db_inst = models.AgentInstance(
        id=str(uuid4()),
        deployment_id=deployment_id,
        status="running",
        handle=handle,
        endpoint=endpoint,
        created_at=datetime.utcnow(),
    )
    db.add(db_inst)
    db.commit()
    db.refresh(db_inst)
    return Instance.model_validate(db_inst)


def update_instance_status(
    db: Session, instance_id: str, status: str
) -> Optional[Instance]:
    obj = db.get(models.AgentInstance, instance_id)
    if obj is None:
        return None
    obj.status = status
    if status in {"stopped", "failed"}:
        obj.stopped_at = datetime.utcnow()
    db.commit()
    db.refresh(obj)
    return Instance.model_validate(obj)
