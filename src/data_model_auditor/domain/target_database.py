"""Database the audited model targets. The application itself uses no database."""

from enum import StrEnum


class TargetDatabase(StrEnum):
    """Destination DBMS chosen for the audit."""

    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"


_ERWIN_TARGET_SERVER = {
    "172": TargetDatabase.SQLSERVER,
    "174": TargetDatabase.ORACLE,
}


def target_from_erwin(code: str) -> TargetDatabase | None:
    """Map the Erwin ``Target_Server`` code when it is a supported destination.

    Codes come from the Erwin metamodel. Unknown codes return ``None`` so the
    user chooses the destination instead of the application guessing it.
    """
    return _ERWIN_TARGET_SERVER.get(code.strip())
