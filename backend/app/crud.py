# backend/app/crud.py
from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from . import models
from .schemas import AgentCardCreate, AgentCard, LocationCreate, Location, DeploymentCreate, Deployment, Instance


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

def create_deployment(
    db: Session,
    dep_in: DeploymentCreate,
    local_path: Optional[str] = None,
    status: str = "requested",
    metadata: Optional[dict] = None,
) -> Optional[Deployment]:
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
        # Update in-place
        if local_path is not None:
            existing.local_path = local_path
        existing.status = status
        if metadata:
            # assuming you used "meta" on the ORM model
            if existing.meta is None:
                existing.meta = metadata
            else:
                existing.meta.update(metadata)
        db.commit()
        db.refresh(existing)
        return Deployment.model_validate(existing)

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
    return Deployment.model_validate(db_dep)

def list_deployments_for_agent(
    db: Session, agent_id: str
) -> List[Deployment]:
    objs = (
        db.query(models.Deployment)
        .filter(models.Deployment.agent_id == agent_id)
        .order_by(models.Deployment.created_at.desc())
        .all()
    )
    return [Deployment.model_validate(o) for o in objs]


def get_latest_ready_deployment(
    db: Session, agent_id: str, location_id: str
) -> Optional[Deployment]:
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
    return Deployment.model_validate(obj) if obj else None


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
