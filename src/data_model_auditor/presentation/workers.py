"""Run slow use cases off the interface thread."""

import logging
from collections.abc import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from data_model_auditor.application.audit_workflow import InputFileError
from data_model_auditor.domain.audit_scope import SubjectAreaSelectionError
from data_model_auditor.domain.rule_catalog import RuleConfigurationError

_LOGGER = logging.getLogger(__name__)
_EXPECTED = (InputFileError, RuleConfigurationError, SubjectAreaSelectionError)
_UNEXPECTED_MESSAGE = "Ocorreu um erro inesperado. Consulte o arquivo de log da aplicação."


class _Signals(QObject):
    succeeded = Signal(object)
    failed = Signal(str)


class _Task(QRunnable):
    def __init__(self, work: Callable[[], object], signals: _Signals) -> None:
        super().__init__()
        self._work = work
        self._signals = signals

    def run(self) -> None:
        try:
            result = self._work()
        except _EXPECTED as exc:
            self._signals.failed.emit(str(exc))
            return
        except Exception:
            # The worker thread must report every failure back to the window.
            _LOGGER.exception("Background task failed")
            self._signals.failed.emit(_UNEXPECTED_MESSAGE)
            return
        self._signals.succeeded.emit(result)


class BackgroundRunner(QObject):
    """Start one task at a time and deliver the result on the interface thread."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._pool = QThreadPool(self)
        self._pool.setMaxThreadCount(1)
        self._signals: _Signals | None = None

    def start(
        self,
        work: Callable[[], object],
        on_success: Callable[[object], None],
        on_failure: Callable[[str], None],
    ) -> None:
        """Run ``work`` in the pool and call one of the callbacks afterwards."""
        signals = _Signals()
        signals.succeeded.connect(on_success)
        signals.failed.connect(on_failure)
        self._signals = signals
        self._pool.start(_Task(work, signals))

    def wait(self) -> None:
        """Block until the running task finishes. Used when closing the window."""
        self._pool.waitForDone()
