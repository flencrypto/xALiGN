"""EstimatingProject, ScopeGapItem, and ChecklistItem SQLAlchemy models."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class ProjectType(str, enum.Enum):
    live_refurb = "live_refurb"
    brownfield = "brownfield"
    new_build = "new_build"


class ScopeGapCategory(str, enum.Enum):
    enabling_works = "enabling_works"
    temp_power = "temp_power"
    temp_cooling = "temp_cooling"
    weekend_working = "weekend_working"
    commissioning = "commissioning"
    client_kit = "client_kit"
    logistics = "logistics"
    permits = "permits"


class EstimatingProject(Base):
    """The estimating context for a bid, tracking scope and cost."""

    __tablename__ = "estimating_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False
    )
    project_type: Mapped[ProjectType] = mapped_column(
        Enum(ProjectType, name="estimating_project_type"), nullable=False
    )
    tier_level: Mapped[str | None] = mapped_column(String(10))
    total_budget: Mapped[float | None] = mapped_column(Float)
    contingency_pct: Mapped[float | None] = mapped_column(Float, default=10.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    bid: Mapped["Bid"] = relationship("Bid", back_populates="estimating_projects")  # type: ignore[name-defined]
    scope_gap_items: Mapped[list["ScopeGapItem"]] = relationship(
        "ScopeGapItem", back_populates="project", cascade="all, delete-orphan"
    )
    checklist_items: Mapped[list["ChecklistItem"]] = relationship(
        "ChecklistItem", back_populates="project", cascade="all, delete-orphan"
    )


class ScopeGapItem(Base):
    """A potential scope gap that could affect pricing or delivery."""

    __tablename__ = "scope_gap_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("estimating_projects.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[ScopeGapCategory] = mapped_column(Enum(ScopeGapCategory), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    identified: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_agreed: Mapped[bool] = mapped_column(Boolean, default=False)
    included_in_price: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    project: Mapped["EstimatingProject"] = relationship(
        "EstimatingProject", back_populates="scope_gap_items"
    )


class ChecklistItem(Base):
    """A checklist item for the estimating process."""

    __tablename__ = "checklist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("estimating_projects.id", ondelete="CASCADE"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    item: Mapped[str] = mapped_column(Text, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text)

    project: Mapped["EstimatingProject"] = relationship(
        "EstimatingProject", back_populates="checklist_items"
    )
