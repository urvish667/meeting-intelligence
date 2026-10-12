import asyncio
from typing import Optional
from app.db.session import SessionLocal
from app.db.repositories.meeting_repo import MeetingRepository
from app.services.transcription.faster_whisper import FasterWhisperProvider
from app.services.transcription.base import TranscriptionProvider
from app.services.analysis.llm_analyzer import GeminiAnalyzerProvider
from app.services.analysis.base import LLMAnalyzerProvider
from app.core.config import settings
from app.core.logging import logger


class ProcessingPipeline:
    def __init__(
        self,
        transcription_provider: Optional[TranscriptionProvider] = None,
        analysis_provider: Optional[LLMAnalyzerProvider] = None
    ):
        self.transcription_provider = transcription_provider or FasterWhisperProvider()
        self.analysis_provider = analysis_provider or GeminiAnalyzerProvider()

    def process_meeting_sync(self, meeting_id: str):
        db = SessionLocal()
        repo = MeetingRepository(db)
        try:
            meeting = repo.get_by_id(meeting_id)
            if not meeting:
                logger.error(f"Meeting {meeting_id} not found for processing")
                return
            repo.update_status(meeting_id, "transcribing")
            logger.info(f"Meeting {meeting_id}: Starting transcription")
            
            transcription_res = self.transcription_provider.transcribe(meeting.storage_path)
            
            segments_payload = [seg.model_dump() for seg in transcription_res.segments]
            repo.save_transcription(
                meeting_id=meeting_id,
                segments_data=segments_payload,
                language=transcription_res.language,
                duration_seconds=transcription_res.duration_seconds,
                provider=transcription_res.provider,
                model=transcription_res.model
            )
            logger.info(f"Meeting {meeting_id}: Transcription complete ({len(segments_payload)} segments)")

            repo.update_status(meeting_id, "analyzing")
            logger.info(f"Meeting {meeting_id}: Starting AI analysis")

            try:
                analysis = self.analysis_provider.analyze_transcript(
                    transcript_text=transcription_res.full_text,
                    segments=segments_payload
                )
                repo.save_analysis(
                    meeting_id=meeting_id,
                    summary=analysis.summary,
                    structured_payload=analysis.model_dump(),
                    provider="gemini",
                    model=getattr(self.analysis_provider, "model_name", settings.gemini_model)
                )
                repo.update_status(meeting_id, "completed")
                logger.info(f"Meeting {meeting_id}: Processing fully completed")
            except Exception as analysis_err:
                logger.warning(f"Meeting {meeting_id}: AI analysis failed: {analysis_err}")
                repo.update_status(meeting_id, "failed", error_message=f"Analysis failed: {str(analysis_err)}")

        except Exception as e:
            logger.error(f"Meeting {meeting_id}: Pipeline failed: {e}", exc_info=True)
            repo.update_status(meeting_id, "failed", error_message=str(e))
        finally:
            db.close()

    async def run(self, meeting_id: str):
        await asyncio.to_thread(self.process_meeting_sync, meeting_id)


pipeline = ProcessingPipeline()
