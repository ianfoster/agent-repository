from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


class IOField(BaseModel):
    """
    Description of a single input or output field for an agent.
    """
    description: str
    type: str = "string"          # e.g., "string", "float", "json", "file"
    required: bool = True
    default: Optional[Any] = None


# ----------------------------
# A2A Agent Card models
# ----------------------------

class A2ASkill(BaseModel):
    """
    A2A skill description, simplified from the A2A Agent Card spec.
    """
    id: str
    name: str
    description: Optional[str] = None
    tags: List[str] = []
    inputModes: List[str] = []
    outputModes: List[str] = []
    examples: List[Any] = []


class A2AAgentCard(BaseModel):
    """
    A2A Agent Card metadata, aligned with the A2A specification.
    """
    name: str
    url: str
    description: Optional[str] = None
    version: str
    protocolVersion: Optional[str] = None

    capabilities: Dict[str, Any] = Field(default_factory=dict)
    skills: List[A2ASkill] = Field(default_factory=list)

    defaultInputModes: List[str] = Field(default_factory=list)
    defaultOutputModes: List[str] = Field(default_factory=list)
    supportsAuthenticatedExtendedCard: bool = False

    securitySchemes: Optional[Dict[str, Any]] = None
    security: Optional[List[Dict[str, Any]]] = None


# ----------------------------
# Core Agent models
# ----------------------------

class AgentBase(BaseModel):
    """
    Shared fields for created and stored agents.
    """
    model_config = ConfigDict(from_attributes=True)

    name: str
    version: str
    description: str

    agent_type: str               # "task", "domain", "planner", "tool-wrapper", etc.
    tags: List[str] = []

    inputs: Dict[str, IOField]
    outputs: Dict[str, IOField]

    owner: Optional[str] = None   # user or team id

    # Optional A2A Agent Card metadata
    a2a_card: Optional[A2AAgentCard] = None

    # GitHub / container metadata
    git_repo: Optional[str] = None
    git_commit: Optional[str] = None
    container_image: Optional[str] = None
    entrypoint: Optional[str] = None

    # Validation / evaluation metadata
    validation_status: str = "unvalidated"  # "unvalidated", "validated", "failed", etc.
    last_validated_at: Optional[datetime] = None
    validation_score: Optional[float] = None


class AgentCreate(AgentBase):
    """
    Payload for creating a new agent.
    """
    pass


class AgentSpec(AgentBase):
    """
    Full representation of an agent as stored in the repository.
    """
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ----------------------------
# Deployment models
# ----------------------------

class DeploymentCreate(BaseModel):
    """
    Request body when asking to deploy an agent.
    For the stub, we just capture a logical target.
    """
    target: str = Field(..., description="Logical deployment target, e.g., 'dev', 'hpc', 'lab-node-1'")


class Deployment(BaseModel):
    """
    Representation of a deployment record returned by the API.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    agent_id: UUID
    target: str
    status: str
    created_at: datetime

class RunRequest(BaseModel):
    """
    Request body for running an agent locally via the backend.
    For now, inputs are optional and default to an empty dict.
    """
    inputs: Dict[str, Any] = Field(default_factory=dict)
    target: str = Field(
        default="local-ui",
        description="Logical deployment target, used when recording a deployment",
    )


class RunResult(BaseModel):
    """
    Response from /agents/{id}/run.
    """
    outputs: Dict[str, Any]
    deployment: Optional[Deployment] = None
