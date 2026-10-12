import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import av
from app.core.config import settings
from app.core.errors import AppException

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".ogg", ".flac"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/wave", "audio/x-pn-wav", "audio/m4a", "audio/x-m4a",
    "audio/ogg", "audio/flac", "application/octet-stream"
}


def calculate_checksum(file_path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest()


def validate_audio_file(file_path: Path, filename: str, content_type: str = "") -> Dict[str, Any]:
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise AppException(f"Unsupported file format '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}", 415)

    size = file_path.stat().st_size
    if size == 0:
        raise AppException("Uploaded audio file is empty", 400)

    max_bytes = settings.max_upload_mb * 1024 * 1024
    if size > max_bytes:
        raise AppException(f"File size exceeds maximum allowed limit of {settings.max_upload_mb} MB", 413)

    try:
        with av.open(str(file_path)) as container:
            audio_streams = [s for s in container.streams if s.type == "audio"]
            if not audio_streams:
                raise AppException("No audio stream found in the uploaded file", 400)
            
            stream = audio_streams[0]
            duration = None
            if container.duration is not None and container.duration > 0:
                duration = round(float(container.duration / av.time_base), 2)

            return {
                "size_bytes": size,
                "duration_seconds": duration,
                "channels": getattr(stream, "channels", None),
                "rate": getattr(stream, "rate", None),
            }
    except AppException:
        raise
    except Exception as e:
        raise AppException(f"Failed to decode audio file. Corrupted or invalid audio format: {str(e)}", 400)
