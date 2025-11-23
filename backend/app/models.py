from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import DateTime, JSON, String, Text
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
    )  # store UUID as string for DB portability

    name: Mapped[str] = mapped_column(String(255), index=True)
    version: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    agent_type: Mapped[str] = mapped_column(String(50), index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    owner: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)

    a2a_card: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

