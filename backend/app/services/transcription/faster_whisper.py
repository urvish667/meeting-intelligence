from pathlib import Path
from typing import Optional
import av

_orig_av_open = av.open


def _compat_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)


av.open = _compat_av_open

from faster_whisper import WhisperModel
from app.services.transcription.base import TranscriptionProvider, TranscriptionResult, SegmentData
from app.core.logging import logger
from app.core.config import settings


class FasterWhisperProvider(TranscriptionProvider):
    def __init__(
        self,
        model_size: str = settings.whisper_model_size,
        device: str = settings.whisper_device,
        compute_type: str = settings.whisper_compute_type
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    def _get_model(self) -> WhisperModel:
        if self._model is None:
            logger.info(f"Loading faster-whisper model: {self.model_size} ({self.device}, {self.compute_type})")
            self._model = WhisperModel(self.model_size, device=self.device, compute_type=self.compute_type)
        return self._model

    def transcribe(self, audio_path: str) -> TranscriptionResult:
        model = self._get_model()
        logger.info(f"Transcribing audio file: {audio_path}")
        segments_gen, info = model.transcribe(str(audio_path), beam_size=5)

        segments = []
        full_text_parts = []
        for s in segments_gen:
            text = s.text.strip()
            if text:
                full_text_parts.append(text)
                confidence = round(float(s.avg_logprob), 3) if hasattr(s, "avg_logprob") else None
                segments.append(SegmentData(
                    start_seconds=round(float(s.start), 2),
                    end_seconds=round(float(s.end), 2),
                    text=text,
                    speaker=None,
                    confidence=confidence
                ))

        return TranscriptionResult(
            segments=segments,
            full_text=" ".join(full_text_parts),
            language=getattr(info, "language", None),
            duration_seconds=round(float(info.duration), 2) if hasattr(info, "duration") else None,
            provider="faster-whisper",
            model=self.model_size
        )
