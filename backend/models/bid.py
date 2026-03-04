"""Bid, BidDocument, ComplianceItem, and RFI SQLAlchemy models."""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class BidStatus(str, enum.Enum):
    draft = "draft"
    review = "review"
    submitted = "submitted"
    won = "won"
    lost = "lost"


class DocType(str, enum.Enum):
    tender = "tender"
    method_statement = "method_statement"
    programme = "programme"
    risk_register = "risk_register"
    compliance_matrix = "compliance_matrix"


class ComplianceStatus(str, enum.Enum):
    yes = "yes"
    partial = "partial"
    no = "no"
    tbc = "tbc"


class RFIPriority(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class RFIStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    answered = "answered"


class Bid(Base):
    """A bid submission for an opportunity."""

    __tablename__ = "bids"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    opportunity_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    tender_ref: Mapped[str | None] = mapped_column(String(100), index=True)
    submission_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[BidStatus] = mapped_column(
        Enum(BidStatus), default=BidStatus.draft, server_default="draft"
    )
    win_themes: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), server_default=func.now()
    )

    opportunity: Mapped["Opportunity"] = relationship("Opportunity", back_populates="bids")  # type: ignore[name-defined]
    documents: Mapped[list["BidDocument"]] = relationship(
        "BidDocument", back_populates="bid", cascade="all, delete-orphan"
    )
    compliance_items: Mapped[list["ComplianceItem"]] = relationship(
        "ComplianceItem", back_populates="bid", cascade="all, delete-orphan"
    )
    rfis: Mapped[list["RFI"]] = relationship(
        "RFI", back_populates="bid", cascade="all, delete-orphan"
    )
    estimating_projects: Mapped[list] = relationship(
        "EstimatingProject", back_populates="bid", cascade="all, delete-orphan"
    )
    debrief: Mapped["BidDebrief | None"] = relationship(  # type: ignore[name-defined]
        "BidDebrief", back_populates="bid", cascade="all, delete-orphan", uselist=False
    )


class BidDocument(Base):
    """A document uploaded as part of the bid pack."""

    __tablename__ = "bid_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    doc_type: Mapped[DocType] = mapped_column(Enum(DocType), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text)
    extracted_requirements: Mapped[str | None] = mapped_column(Text)  # stored as JSON string
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), server_default=func.now()
    )

    bid: Mapped["Bid"] = relationship("Bid", back_populates="documents")


class ComplianceItem(Base):
    """A single compliance requirement derived from tender documents."""

    __tablename__ = "compliance_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False
    )
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    compliance_status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus), default=ComplianceStatus.tbc, server_default="tbc"
    )
    evidence: Mapped[str | None] = mapped_column(Text)
    owner: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)

    bid: Mapped["Bid"] = relationship("Bid", back_populates="compliance_items")


class RFI(Base):
    """A Request for Information raised during bid preparation."""

    __tablename__ = "rfis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    bid_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("bids.id", ondelete="CASCADE"), nullable=False
    )
    question: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(100))
    priority: Mapped[RFIPriority] = mapped_column(
        Enum(RFIPriority), default=RFIPriority.medium, server_default="medium"
    )
    status: Mapped[RFIStatus] = mapped_column(
        Enum(RFIStatus), default=RFIStatus.draft, server_default="draft"
    )
    answer: Mapped[str | None] = mapped_column(Text)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime)

    bid: Mapped["Bid"] = relationship("Bid", back_populates="rfis")
