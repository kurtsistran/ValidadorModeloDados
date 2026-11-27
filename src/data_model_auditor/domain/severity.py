"""Severity levels used by validation findings."""

from enum import StrEnum


class Severity(StrEnum):
    """How serious a validation finding is."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
