from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, func, or_
from app.db.models import Meeting, TranscriptSegment, MeetingAnalysis, MeetingQuery, utc_now


class MeetingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        id: str,
        original_filename: str,
        storage_path: str,
        content_type: str,
        size_bytes: int,
        checksum: str,
        duration_seconds: Optional[float] = None
    ) -> Meeting:
        meeting = Meeting(
            id=id,
            original_filename=original_filename,
            storage_path=storage_path,
            content_type=content_type,
            size_bytes=size_bytes,
            checksum=checksum,
            duration_seconds=duration_seconds,
            status="uploaded",
        )
        self.db.add(meeting)
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def get_by_id(self, meeting_id: str) -> Optional[Meeting]:
        stmt = select(Meeting).where(Meeting.id == meeting_id)
        return self.db.scalars(stmt).first()

    def get_by_checksum(self, checksum: str) -> Optional[Meeting]:
        stmt = select(Meeting).where(Meeting.checksum == checksum)
        return self.db.scalars(stmt).first()

    def list_meetings(
        self,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        query: Optional[str] = None
    ) -> Tuple[List[Meeting], int]:
        stmt = select(Meeting)
        if status:
            stmt = stmt.where(Meeting.status == status)
        if query:
            stmt = stmt.where(Meeting.original_filename.ilike(f"%{query}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.db.scalar(count_stmt) or 0

        stmt = stmt.order_by(Meeting.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        items = list(self.db.scalars(stmt).all())
        return items, total

    def update_status(
        self,
        meeting_id: str,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Meeting]:
        meeting = self.get_by_id(meeting_id)
        if not meeting:
            return None
        meeting.status = status
        meeting.error_message = error_message
        now = utc_now()
        meeting.updated_at = now
        if status == "transcribing":
            meeting.transcription_started_at = now
        elif status == "analyzing":
            meeting.transcription_completed_at = now
            meeting.analysis_started_at = now
        elif status == "completed":
            meeting.analysis_completed_at = now
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def save_transcription(
        self,
        meeting_id: str,
        segments_data: List[dict],
        language: Optional[str],
        duration_seconds: Optional[float],
        provider: str,
        model: str
    ):
        meeting = self.get_by_id(meeting_id)
        if not meeting:
            return None
        for s in list(meeting.segments):
            self.db.delete(s)
        self.db.flush()

        for idx, seg in enumerate(segments_data):
            segment = TranscriptSegment(
                meeting_id=meeting_id,
                segment_index=idx,
                start_seconds=seg.get("start_seconds", 0.0),
                end_seconds=seg.get("end_seconds", 0.0),
                text=seg.get("text", "").strip(),
                speaker=seg.get("speaker"),
                confidence=seg.get("confidence")
            )
            self.db.add(segment)

        meeting.language = language
        if duration_seconds:
            meeting.duration_seconds = duration_seconds
        meeting.transcription_provider = provider
        meeting.transcription_model = model
        self.db.commit()
        self.db.refresh(meeting)
        return meeting

    def save_analysis(
        self,
        meeting_id: str,
        summary: str,
        structured_payload: dict,
        provider: str,
        model: str,
        prompt_version: str = "v1"
    ) -> MeetingAnalysis:
        meeting = self.get_by_id(meeting_id)
        if not meeting:
            raise ValueError("Meeting not found")

        if meeting.analysis:
            self.db.delete(meeting.analysis)
            self.db.flush()

        analysis = MeetingAnalysis(
            meeting_id=meeting_id,
            summary=summary,
            structured_payload=structured_payload,
            provider=provider,
            model=model,
            prompt_version=prompt_version
        )
        self.db.add(analysis)
        meeting.analysis_provider = provider
        meeting.analysis_model = model
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def add_query(
        self,
        meeting_id: str,
        question: str,
        answer: str,
        evidence: list,
        provider: str,
        model: str
    ) -> MeetingQuery:
        query = MeetingQuery(
            meeting_id=meeting_id,
            question=question,
            answer=answer,
            evidence=evidence,
            provider=provider,
            model=model
        )
        self.db.add(query)
        self.db.commit()
        self.db.refresh(query)
        return query

    def delete(self, meeting_id: str) -> Optional[Meeting]:
        meeting = self.get_by_id(meeting_id)
        if not meeting:
            return None
        self.db.delete(meeting)
        self.db.commit()
        return meeting
