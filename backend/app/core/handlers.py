import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.exceptions import AppError, InvalidRequestError
from app.core.schemas import ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)

HTTP_ERROR_CODES = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
REQUEST_PARTS = ("query", "path", "body")


def error_response(status_code: int, code: str, message: str) -> JSONResponse:
    body = ErrorResponse(error=ErrorDetail(code=code, message=message))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message)


async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    message = InvalidRequestError.message
    if errors := exc.errors():
        first = errors[0]
        field = ".".join(str(part) for part in first["loc"] if part not in REQUEST_PARTS)
        message = f"{field}: {first['msg']}" if field else first["msg"]
    return error_response(InvalidRequestError.status_code, InvalidRequestError.code, message)


async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = HTTP_ERROR_CODES.get(exc.status_code, "HTTP_ERROR")
    return error_response(exc.status_code, code, str(exc.detail))


class UnhandledErrorMiddleware:
    """Turns any unexpected exception into a clean 500."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        started = False

        async def tracked_send(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self.app(scope, receive, tracked_send)
        except Exception:
            logger.exception("Unhandled error on %s %s", scope["method"], scope["path"])
            if started:
                raise
            response = error_response(AppError.status_code, AppError.code, AppError.message)
            await response(scope, receive, send)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_error_handler)
