# backend/app/models.py
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class AgentImplementation(Base):
    """
    Agent implementation = Agent Card for a single name/version.

    This corresponds to your (A): an implementation in GitHub
    that is (or should be) an Academy Agent.
    """
    __tablename__ = "agent_implementations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50), index=True)

    description: Mapped[str] = mapped_column(Text)
    agent_type: Mapped[str] = mapped_column(String(50))  # task, workflow, planner, etc.

    # Metadata & schema
    tags: Mapped[list[str]] = mapped_column(JSON, default=list)
    inputs_schema: Mapped[dict] = mapped_column(JSON, default=dict)
    outputs_schema: Mapped[dict] = mapped_column(JSON, default=dict)

    # Academy / implementation metadata
    git_repo: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    git_commit: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    container_image: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    entrypoint: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)  # module:Class

    # Optional validation inputs (for simple validation runs)
    validation_inputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Validation state (global, across deployments)
    validation_status: Mapped[str] = mapped_column(String(32), default="unvalidated")
    validation_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    last_validated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class Location(Base):
    """
    Location = (B): place where agents can be deployed and started.

    Encodes Academy Exchange/Manager config (conceptually).
    """
    __tablename__ = "locations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)

    # e.g., local | hpc | lab | cloud
    location_type: Mapped[str] = mapped_column(String(32))

    # Arbitrary config used by runtime/Academy to create Manager+Exchange.
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    # Whether new deployments are allowed here
    is_active: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    deployments: Mapped[list["Deployment"]] = relationship(
        back_populates="location", cascade="all, delete-orphan"
    )


class AgentInstance(Base):
    """
    Running agent (C): a live instance started from a Deployment at a Location.

    Represents an Academy Agent handle or equivalent runtime identifier.
    """
    __tablename__ = "agent_instances"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    deployment_id: Mapped[str] = mapped_column(ForeignKey("deployments.id"))

    # e.g., starting | running | stopped | failed
    status: Mapped[str] = mapped_column(String(32), default="starting")

    # Some opaque handle from Academy: could be serialized AgentHandle, URL, etc.
    handle: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    # Optional endpoint info (HTTP URL, socket addr, etc.)
    endpoint: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    deployment: Mapped[Deployment] = relationship(back_populates="instances")
