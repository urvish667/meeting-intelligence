import uuid
import re
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, Query
from app.api.deps import get_repository, get_pipeline
from app.db.repositories.meeting_repo import MeetingRepository
from app.services.pipeline import ProcessingPipeline
from app.core.config import settings
from app.core.errors import AppException, NotFoundError, DuplicateAudioError
from app.services.audio_validation import validate_audio_file, calculate_checksum
from app.schemas.meeting import (
    MeetingUploadResponse,
    MeetingListResponse,
    MeetingListItem,
    MeetingDetail,
)

router = APIRouter(prefix="/meetings", tags=["meetings"])


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\.-]", "_", Path(filename).name)
    return cleaned or "audio_file"


@router.post("/upload", response_model=MeetingUploadResponse, status_code=202)
async def upload_meeting(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    repo: MeetingRepository = Depends(get_repository),
    pipeline: ProcessingPipeline = Depends(get_pipeline)
):
    if not file.filename:
        raise AppException("Filename cannot be empty", 400)

    meeting_id = str(uuid.uuid4())
    safe_name = sanitize_filename(file.filename)
    target_path = settings.storage_path / f"{meeting_id}_{safe_name}"

    try:
        with open(target_path, "wb") as f:
            while chunk := await file.read(1024 * 1024):
                f.write(chunk)
    except Exception as e:
        if target_path.exists():
            target_path.unlink()
        raise AppException(f"Failed to save uploaded file: {str(e)}", 500)

    try:
        validation_info = validate_audio_file(
            file_path=target_path,
            filename=file.filename,
            content_type=file.content_type or ""
        )
        checksum = calculate_checksum(target_path)
    except AppException:
        if target_path.exists():
            target_path.unlink()
        raise

    existing = repo.get_by_checksum(checksum)
    if existing:
        if target_path.exists():
            target_path.unlink()
        raise DuplicateAudioError(
            f"An identical audio file already exists for meeting ID {existing.id} (Status: {existing.status}).",
            existing_id=existing.id
        )

    meeting = repo.create(
        id=meeting_id,
        original_filename=file.filename,
        storage_path=str(target_path),
        content_type=file.content_type or "audio/mpeg",
        size_bytes=validation_info["size_bytes"],
        checksum=checksum,
        duration_seconds=validation_info.get("duration_seconds")
    )

    background_tasks.add_task(pipeline.run, meeting_id)

    return MeetingUploadResponse(
        id=meeting.id,
        original_filename=meeting.original_filename,
        status=meeting.status,
        message="Audio uploaded successfully. Transcription and AI analysis initiated."
    )


@router.get("", response_model=MeetingListResponse)
def list_meetings(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    repo: MeetingRepository = Depends(get_repository)
):
    items, total = repo.list_meetings(page=page, page_size=page_size, status=status, query=query)
    return MeetingListResponse(
        items=[MeetingListItem.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting(
    meeting_id: str,
    repo: MeetingRepository = Depends(get_repository)
):
    meeting = repo.get_by_id(meeting_id)
    if not meeting:
        raise NotFoundError(f"Meeting {meeting_id} not found")

    detail = MeetingDetail.model_validate(meeting)
    detail.full_transcript = " ".join([s.text for s in meeting.segments])
    return detail


@router.delete("/{meeting_id}")
def delete_meeting(
    meeting_id: str,
    repo: MeetingRepository = Depends(get_repository)
):
    meeting = repo.get_by_id(meeting_id)
    if not meeting:
        raise NotFoundError(f"Meeting {meeting_id} not found")

    file_path = Path(meeting.storage_path)
    if file_path.exists():
        try:
            file_path.unlink()
        except Exception:
            pass

    repo.delete(meeting_id)
    return {"message": f"Meeting {meeting_id} deleted successfully"}


@router.post("/{meeting_id}/reprocess")
def reprocess_meeting(
    meeting_id: str,
    background_tasks: BackgroundTasks,
    repo: MeetingRepository = Depends(get_repository),
    pipeline: ProcessingPipeline = Depends(get_pipeline)
):
    meeting = repo.get_by_id(meeting_id)
    if not meeting:
        raise NotFoundError(f"Meeting {meeting_id} not found")

    if not Path(meeting.storage_path).exists():
        raise AppException("Original audio file is missing from server storage.", 404)

    repo.update_status(meeting_id, "uploaded", error_message=None)
    background_tasks.add_task(pipeline.run, meeting_id)
    return {"message": f"Reprocessing started for meeting {meeting_id}", "status": "uploaded"}
