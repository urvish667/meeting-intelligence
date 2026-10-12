from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class DuplicateAudioError(AppException):
    def __init__(self, message: str = "Duplicate audio file detected", existing_id: str = ""):
        super().__init__(message, status_code=409)
        self.existing_id = existing_id


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        payload = {"detail": exc.message}
        if isinstance(exc, DuplicateAudioError) and exc.existing_id:
            payload["existing_id"] = exc.existing_id
        return JSONResponse(status_code=exc.status_code, content=payload)
