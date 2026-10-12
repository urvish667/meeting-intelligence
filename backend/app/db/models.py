import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, Float, Text, ForeignKey, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded", index=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    transcription_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    transcription_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    analysis_completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    transcription_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    transcription_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analysis_provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    analysis_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    segments: Mapped[List["TranscriptSegment"]] = relationship(
        "TranscriptSegment",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="TranscriptSegment.segment_index"
    )
    analysis: Mapped[Optional["MeetingAnalysis"]] = relationship(
        "MeetingAnalysis",
        back_populates="meeting",
        uselist=False,
        cascade="all, delete-orphan"
    )
    queries: Mapped[List["MeetingQuery"]] = relationship(
        "MeetingQuery",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="MeetingQuery.created_at.desc()"
    )


class TranscriptSegment(Base):
    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)
    start_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    end_seconds: Mapped[float] = mapped_column(Float, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    speaker: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="segments")


class MeetingAnalysis(Base):
    __tablename__ = "meeting_analyses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), unique=True, index=True)
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="analysis")


class MeetingQuery(Base):
    __tablename__ = "meeting_queries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    meeting_id: Mapped[str] = mapped_column(String(36), ForeignKey("meetings.id", ondelete="CASCADE"), index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    meeting: Mapped["Meeting"] = relationship("Meeting", back_populates="queries")
