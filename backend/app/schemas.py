from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IOField(BaseModel):
    """
    Description of a single input or output field for an agent.
    """
    description: str
    type: str = "string"          # e.g., "string", "float", "json", "file"
    required: bool = True
    default: Optional[Any] = None


class AgentBase(BaseModel):
    """
    Shared fields for created and stored agents.
    """
    name: str
    version: str
    description: str

    agent_type: str               # "task", "domain", "planner", "tool-wrapper", etc.
    tags: List[str] = []

    inputs: Dict[str, IOField]
    outputs: Dict[str, IOField]

    owner: Optional[str] = None   # user or team id


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

