from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, JSON, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base

from sqlalchemy import String, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

class AgentImplementation(Base):
    """
    SQLAlchemy ORM model for agents.
    Nested structures (tags, inputs, outputs, a2a_card) are stored as JSON.
    """
    __tablename__ = "agent_implementations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50), index=True)

    description: Mapped[str] = mapped_column(Text)
    agent_type: Mapped[str] = mapped_column(String(50))

    # NEW: schemas for inputs/outputs
    inputs_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    outputs_schema: Mapped[dict] = mapped_column(JSON, default=dict)

    # You may also want tags stored as JSON if you use them:
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    # optional default validation inputs (for simple smoke tests)
    validation_inputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    git_repo: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    container_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    entrypoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # validation-related fields if you use them:
    validation_status: Mapped[str] = mapped_column(String(32), default="unvalidated")
    validation_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

class AgentImplementation_old(Base):

    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    agent_type: Mapped[str] = mapped_column(String(50), index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    owner: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    a2a_card: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    # GitHub / container metadata
    git_repo: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    container_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    entrypoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)

    # Validation / evaluation metadata
    validation_status: Mapped[str] = mapped_column(String(32), default="unvalidated", nullable=False)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    validation_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class Deployment(Base):
    __tablename__ = "deployments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(36), index=True)
    location_id: Mapped[str] = mapped_column(String(36), index=True)

    status: Mapped[str] = mapped_column(String(32), default="requested")
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    local_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

class Location(Base):
    """
    Location = where agents can be deployed and run.

    This is your (B): local, HPC, lab, cloud, etc.
    """
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # e.g., "local", "hpc", "lab", "cloud"
    location_type: Mapped[str] = mapped_column(String(32), default="local")

    # Arbitrary config for the runtime / Academy Manager+Exchange
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
