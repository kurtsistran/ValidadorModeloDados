"""Versioned HTTP routes. These handlers do not contain audit rules."""

from fastapi import APIRouter
from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response for the process health check."""

    status: str


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    """Report that the API process is accepting requests."""
    return HealthResponse(status="ok")
