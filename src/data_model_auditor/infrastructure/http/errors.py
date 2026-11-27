"""Standard error responses for the HTTP boundary."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException

logger = logging.getLogger(__name__)


class ErrorBody(BaseModel):
    """Error payload returned by every failed HTTP request."""

    code: str
    message: str
    details: list[str]


def register_exception_handlers(app: FastAPI) -> None:
    """Replace framework error bodies with the project error contract."""

    @app.exception_handler(HTTPException)
    async def handle_http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        message = exc.detail if isinstance(exc.detail, str) else "The request was rejected."
        body = ErrorBody(code="http_error", message=message, details=[])
        return JSONResponse(status_code=exc.status_code, content=body.model_dump())

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        details = [str(error["msg"]) for error in exc.errors()]
        body = ErrorBody(code="invalid_request", message="The request is invalid.", details=details)
        return JSONResponse(status_code=422, content=body.model_dump())

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled request failure", exc_info=exc)
        body = ErrorBody(
            code="internal_error",
            message="The request could not be completed.",
            details=[],
        )
        return JSONResponse(status_code=500, content=body.model_dump())
