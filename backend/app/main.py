from contextlib import asynccontextmanager
import av

_orig_av_open = av.open


def _compat_av_open(*args, **kwargs):
    kwargs.pop("metadata_errors", None)
    return _orig_av_open(*args, **kwargs)


av.open = _compat_av_open

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.core.errors import setup_exception_handlers
from app.db.base import Base
from app.db.session import engine
from app.api.routes import health, meetings, query


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized successfully.")
    yield


app = FastAPI(
    title="AI Meeting Intelligence & Action Tracker",
    description="End-to-end audio processing, transcription, LLM structured extraction, and grounded Q&A.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

setup_exception_handlers(app)

app.include_router(health.router, prefix="/api")
app.include_router(meetings.router, prefix="/api")
app.include_router(query.router, prefix="/api")
