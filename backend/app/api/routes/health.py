from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.session import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    gemini_ready = bool(settings.gemini_api_key and not settings.gemini_api_key.startswith("your_gemini_api_key"))

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "database": db_ok,
        "transcription_provider": settings.transcription_provider,
        "whisper_model": settings.whisper_model_size,
        "whisper_device": settings.whisper_device,
        "llm_provider": settings.llm_provider,
        "gemini_model": settings.gemini_model,
        "gemini_configured": gemini_ready,
    }
