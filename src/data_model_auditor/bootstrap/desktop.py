"""Start the local desktop application."""

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QStandardPaths, QTimer
from PySide6.QtWidgets import QApplication

from data_model_auditor.bootstrap.desktop_composition import (
    build_audit_workflow,
    default_rules_path,
)
from data_model_auditor.presentation.main_window import MainWindow

_APP_NAME = "Data Model Auditor"
_LOG_BYTES = 1024 * 1024
_LOG_BACKUPS = 3
_SMOKE_TEST_MS = 1500


def _configure_logging() -> Path:
    folder = Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    folder.mkdir(parents=True, exist_ok=True)
    log_file = folder / "data_model_auditor.log"
    handler = RotatingFileHandler(
        log_file, maxBytes=_LOG_BYTES, backupCount=_LOG_BACKUPS, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    logging.basicConfig(level=logging.INFO, handlers=[handler])
    return log_file


def main(argv: list[str] | None = None) -> int:
    """Open the window. ``--smoke-test`` closes it automatically for installer checks."""
    parser = argparse.ArgumentParser(prog="data-model-auditor")
    parser.add_argument("--smoke-test", action="store_true", help=argparse.SUPPRESS)
    arguments = parser.parse_args(argv)
    application = QApplication(sys.argv[:1])
    application.setApplicationName(_APP_NAME)
    log_file = _configure_logging()
    logging.getLogger(__name__).info("Application started; log at %s", log_file)
    window = MainWindow(build_audit_workflow(), default_rules_path())
    window.show()
    if arguments.smoke_test:
        QTimer.singleShot(_SMOKE_TEST_MS, application.quit)
    return application.exec()


if __name__ == "__main__":
    sys.exit(main())
