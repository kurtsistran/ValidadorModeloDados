"""Roles enforced by the backend."""

from enum import StrEnum


class Role(StrEnum):
    """Access profile for a user of the auditor."""

    ADMINISTRATOR = "administrator"
    ANALYST = "analyst"
    VIEWER = "viewer"
