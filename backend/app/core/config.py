from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "sqlite:///./meeting_intelligence.db"
    audio_storage_dir: str = "./storage/audio"
    max_upload_mb: int = 100
    transcription_provider: str = "faster-whisper"
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    llm_provider: str = "gemini"
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-3.8-flash"
    cors_origins: List[str] = ["*"]
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def db_url(self) -> str:
        if "./" in self.database_url:
            return f"sqlite:///{(BASE_DIR / 'meeting_intelligence.db').as_posix()}"
        return self.database_url

    @property
    def storage_path(self) -> Path:
        path = BASE_DIR / "backend" / "storage" / "audio"
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
