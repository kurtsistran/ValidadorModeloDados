"""Application settings loaded from the process environment."""

import os
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum


class Environment(StrEnum):
    """Deployment environment selected by configuration."""

    DEVELOPMENT = "development"
    HOMOLOGATION = "homologation"
    PRODUCTION = "production"


class SettingsError(Exception):
    """Raised when the process environment does not contain usable settings."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Secret values stay in the environment, never in source control."""

    environment: Environment
    api_host: str
    api_port: int
    log_level: str

    @classmethod
    def from_environ(cls, source: Mapping[str, str] | None = None) -> "Settings":
        """Build settings from ``source`` or, by default, the process environment."""
        values = os.environ if source is None else source
        environment = _environment(values.get("APP_ENV", Environment.DEVELOPMENT.value))
        api_host = values.get("API_HOST", "127.0.0.1").strip()
        if not api_host:
            raise SettingsError("API_HOST cannot be empty.")
        return cls(
            environment=environment,
            api_host=api_host,
            api_port=_port(values.get("API_PORT", "8000")),
            log_level=_log_level(values.get("LOG_LEVEL", "INFO")),
        )


def _environment(raw_value: str) -> Environment:
    try:
        return Environment(raw_value.strip().lower())
    except ValueError as error:
        allowed = ", ".join(item.value for item in Environment)
        raise SettingsError(f"APP_ENV must be one of: {allowed}.") from error


def _port(raw_value: str) -> int:
    try:
        port = int(raw_value)
    except ValueError as error:
        raise SettingsError("API_PORT must be an integer.") from error
    if port < 1 or port > 65535:
        raise SettingsError("API_PORT must be between 1 and 65535.")
    return port


def _log_level(raw_value: str) -> str:
    level = raw_value.strip().upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise SettingsError("LOG_LEVEL is not a recognized logging level.")
    return level
