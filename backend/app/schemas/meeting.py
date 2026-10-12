from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict
from app.schemas.analysis import MeetingAnalysisSchema


class TranscriptSegmentRead(BaseModel):
    id: str
    segment_index: int
    start_seconds: float
    end_seconds: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class MeetingListItem(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingAnalysisRead(BaseModel):
    id: str
    schema_version: str
    summary: str
    structured_payload: dict
    provider: str
    model: str
    prompt_version: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingQueryRead(BaseModel):
    id: str
    question: str
    answer: str
    evidence: list
    provider: str
    model: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingDetail(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    language: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transcription_started_at: Optional[datetime] = None
    transcription_completed_at: Optional[datetime] = None
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    transcription_provider: Optional[str] = None
    transcription_model: Optional[str] = None
    analysis_provider: Optional[str] = None
    analysis_model: Optional[str] = None
    full_transcript: str = ""
    segments: List[TranscriptSegmentRead] = []
    analysis: Optional[MeetingAnalysisRead] = None
    queries: List[MeetingQueryRead] = []

    model_config = ConfigDict(from_attributes=True)


class MeetingListResponse(BaseModel):
    items: List[MeetingListItem]
    total: int
    page: int
    page_size: int


class MeetingUploadResponse(BaseModel):
    id: str
    original_filename: str
    status: str
    message: str
