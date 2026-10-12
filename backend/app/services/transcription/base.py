from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel


class SegmentData(BaseModel):
    start_seconds: float
    end_seconds: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None


class TranscriptionResult(BaseModel):
    segments: List[SegmentData]
    full_text: str
    language: Optional[str] = None
    duration_seconds: Optional[float] = None
    provider: str
    model: str


class TranscriptionProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_path: str) -> TranscriptionResult:
        pass
