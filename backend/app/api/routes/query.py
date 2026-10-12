from fastapi import APIRouter, Depends
from app.api.deps import get_repository, get_analyzer
from app.db.repositories.meeting_repo import MeetingRepository
from app.services.analysis.base import LLMAnalyzerProvider
from app.core.config import settings
from app.core.errors import NotFoundError, AppException
from app.schemas.query import QueryRequest, QueryResponse

router = APIRouter(prefix="/meetings", tags=["query"])


@router.post("/{meeting_id}/query", response_model=QueryResponse)
def query_meeting(
    meeting_id: str,
    body: QueryRequest,
    repo: MeetingRepository = Depends(get_repository),
    analyzer: LLMAnalyzerProvider = Depends(get_analyzer)
):
    meeting = repo.get_by_id(meeting_id)
    if not meeting:
        raise NotFoundError(f"Meeting {meeting_id} not found")

    if not meeting.segments and not meeting.analysis:
        raise AppException(
            f"Meeting {meeting_id} has not completed transcription or analysis yet (Current status: {meeting.status}).",
            400
        )

    full_transcript = " ".join([s.text for s in meeting.segments])
    analysis_payload = meeting.analysis.structured_payload if meeting.analysis else {}

    answer, evidence = analyzer.answer_query(
        question=body.question,
        transcript_text=full_transcript,
        analysis_dict=analysis_payload
    )

    model_name = getattr(analyzer, "model_name", settings.gemini_model)

    repo.add_query(
        meeting_id=meeting_id,
        question=body.question,
        answer=answer,
        evidence=evidence,
        provider="gemini",
        model=model_name
    )

    return QueryResponse(
        question=body.question,
        answer=answer,
        evidence=evidence,
        provider="gemini",
        model=model_name
    )
