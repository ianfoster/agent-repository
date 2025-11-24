from __future__ import annotations
from datetime import datetime

from typing import List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from . import models
from .schemas import AgentCreate, AgentSpec


def create_agent(db: Session, agent_in: AgentCreate) -> AgentSpec:
    """
    Create a new agent row and return it as an AgentSpec.
    """
    db_agent = models.Agent(
        id=str(uuid4()),
        name=agent_in.name,
        version=agent_in.version,
        description=agent_in.description,
        agent_type=agent_in.agent_type,
        tags=agent_in.tags,
        inputs={k: v.model_dump() for k, v in agent_in.inputs.items()},
        outputs={k: v.model_dump() for k, v in agent_in.outputs.items()},
        owner=agent_in.owner,
        a2a_card=agent_in.a2a_card.model_dump() if agent_in.a2a_card else None,
        git_repo=agent_in.git_repo,
        git_commit=agent_in.git_commit,
        container_image=agent_in.container_image,
        entrypoint=agent_in.entrypoint,
        validation_status=agent_in.validation_status or "unvalidated",
        last_validated_at=agent_in.last_validated_at,
        validation_score=agent_in.validation_score,
    )
    db.add(db_agent)
    db.commit()
    db.refresh(db_agent)

    return AgentSpec.model_validate(db_agent)


def get_agent(db: Session, agent_id: str) -> Optional[AgentSpec]:
    obj = db.get(models.Agent, agent_id)
    if obj is None:
        return None
    return AgentSpec.model_validate(obj)


def list_agents(
    db: Session,
    name: Optional[str] = None,
    agent_type: Optional[str] = None,
    tag: Optional[str] = None,
    owner: Optional[str] = None,
) -> List[AgentSpec]:
    q = db.query(models.Agent)

    if name is not None:
        q = q.filter(models.Agent.name == name)
    if agent_type is not None:
        q = q.filter(models.Agent.agent_type == agent_type)
    if owner is not None:
        q = q.filter(models.Agent.owner == owner)

    results = q.all()

    if tag is not None:
        results = [a for a in results if a.tags and tag in a.tags]

    return [AgentSpec.model_validate(a) for a in results]

def validate_agent(
    db: Session,
    agent_id: str,
    score: Optional[float] = None,
) -> Optional[AgentSpec]:
    """
    Mark an agent as validated and update validation metadata.
    """
    obj = db.get(models.Agent, agent_id)
    if obj is None:
        return None
    obj.validation_status = "validated"
    obj.last_validated_at = datetime.utcnow()
    if score is not None:
        obj.validation_score = score
    db.commit()
    db.refresh(obj)
    return AgentSpec.model_validate(obj)

