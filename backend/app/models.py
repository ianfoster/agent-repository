from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, JSON, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Agent(Base):
    """
    SQLAlchemy ORM model for agents.
    Nested structures (tags, inputs, outputs, a2a_card) are stored as JSON.
    """

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

