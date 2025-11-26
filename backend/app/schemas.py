# backend/app/schemas.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ---------- Agent Cards ----------

class AgentCardBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    description: str

    agent_type: str
    tags: List[str] = []

    inputs_schema: Dict[str, Any] = Field(default_factory=dict)
    outputs_schema: Dict[str, Any] = Field(default_factory=dict)

    git_repo: Optional[str] = None
    git_commit: Optional[str] = None
    container_image: Optional[str] = None
    entrypoint: Optional[str] = None

    validation_inputs: Optional[Dict[str, Any]] = None

    validation_status: str = "unvalidated"
    validation_score: Optional[float] = None
    last_validated_at: Optional[datetime] = None


class AgentCardCreate(AgentCardBase):
    pass


class AgentCard(AgentCardBase):
    id: UUID
    created_at: datetime
    updated_at: datetime


# ---------- Locations ----------

class LocationBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    location_type: str
    config: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class Location(LocationBase):
    id: UUID
    created_at: datetime


# ---------- Deployments ----------

class DeploymentBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: UUID
    location_id: UUID


class DeploymentCreate(DeploymentBase):
    pass


class Deployment(DeploymentBase):
    id: UUID
    status: str
    last_error: Optional[str]
    local_path: Optional[str]
    meta: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


# ---------- Instances ----------

class InstanceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    deployment_id: UUID


class Instance(InstanceBase):
    id: UUID
    status: str
    handle: Optional[str]
    endpoint: Optional[str]
    created_at: datetime
    last_heartbeat_at: Optional[datetime]
    stopped_at: Optional[datetime]


# ---------- Runtime operations ----------

class RunRequest(BaseModel):
    """
    Request to run an agent (either via instance or one-off).
    """
    inputs: Dict[str, Any] = Field(default_factory=dict)
    target: Optional[str] = None  # location name or ID


class RunResult(BaseModel):
    outputs: Dict[str, Any]
    deployment: Optional[Deployment] = None
    instance: Optional[Instance] = None


class AgentCallRequest(BaseModel):
    """
    Call a running instance's action.
    """
    action: str
    payload: Dict[str, Any] = Field(default_factory=dict)


class AgentCallResponse(BaseModel):
    result: Any


class StartInstanceRequest(BaseModel):
    """
    Request body for starting an Academy-based agent instance.
    """
    # In future, you might accept location name, init params, etc.
    location_name: Optional[str] = None
    init_inputs: Dict[str, Any] = Field(default_factory=dict)


class InstanceResponse(BaseModel):
    """
    Minimal description of a running instance.
    """
    instance_id: str
    agent_id: str
    status: str
