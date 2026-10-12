from fastapi import Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.repositories.meeting_repo import MeetingRepository
from app.services.pipeline import pipeline, ProcessingPipeline
from app.services.analysis.llm_analyzer import GeminiAnalyzerProvider
from app.services.analysis.base import LLMAnalyzerProvider


def get_repository(db: Session = Depends(get_db)) -> MeetingRepository:
    return MeetingRepository(db)


def get_pipeline() -> ProcessingPipeline:
    return pipeline


def get_analyzer() -> LLMAnalyzerProvider:
    return pipeline.analysis_provider
