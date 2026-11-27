"""Tests for environment-based settings."""

import pytest

from data_model_auditor.bootstrap.settings import Environment, Settings, SettingsError


def test_settings_use_documented_defaults() -> None:
    """Missing optional variables fall back to the local development defaults."""
    settings = Settings.from_environ({})

    assert settings.environment is Environment.DEVELOPMENT
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8000
    assert settings.log_level == "INFO"


def test_settings_read_each_environment() -> None:
    """Development, homologation and production are the accepted environments."""
    settings = Settings.from_environ(
        {
            "APP_ENV": "production",
            "API_HOST": "0.0.0.0",
            "API_PORT": "9000",
            "LOG_LEVEL": "warning",
        }
    )

    assert settings.environment is Environment.PRODUCTION
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 9000
    assert settings.log_level == "WARNING"


@pytest.mark.parametrize(
    "values",
    [
        {"APP_ENV": "staging"},
        {"API_PORT": "zero"},
        {"API_PORT": "70000"},
        {"API_HOST": "  "},
        {"LOG_LEVEL": "verbose"},
    ],
)
def test_settings_reject_invalid_values(values: dict[str, str]) -> None:
    """Invalid configuration fails before the application starts."""
    with pytest.raises(SettingsError):
        Settings.from_environ(values)
