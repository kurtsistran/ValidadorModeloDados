"""Compose the desktop workflow with the concrete readers and writers."""

import sys
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

from data_model_auditor.application.audit_workflow import (
    AuditWorkflow,
    InputFileError,
    WorkflowPorts,
)
from data_model_auditor.infrastructure.erwin.repository_xml import (
    ErwinXmlError,
    parse_erwin_repository,
)
from data_model_auditor.infrastructure.files import sha256_of
from data_model_auditor.infrastructure.readers.sm077 import (
    SpecificationLayoutError,
    read_entity_specification,
)
from data_model_auditor.infrastructure.readers.tabular import (
    SpreadsheetLayoutError,
    read_thesaurus,
)
from data_model_auditor.infrastructure.reports.errors import ReportWriteError
from data_model_auditor.infrastructure.reports.excel_report import write_excel_report
from data_model_auditor.infrastructure.reports.pdf_report import write_pdf_report
from data_model_auditor.infrastructure.rules.yaml_rules import load_rule_catalog

_INPUT_ERRORS = (
    ErwinXmlError,
    SpecificationLayoutError,
    SpreadsheetLayoutError,
    ReportWriteError,
    OSError,
)
_DEFAULT_RULES = Path("rules") / "default_rules.yaml"


def _translated[**P, R](function: Callable[P, R]) -> Callable[P, R]:
    """Expose reader and writer failures as one application error."""

    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return function(*args, **kwargs)
        except _INPUT_ERRORS as exc:
            raise InputFileError(str(exc)) from exc

    return wrapper


def default_rules_path() -> Path:
    """Rules shipped next to the executable, or in the source checkout."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / _DEFAULT_RULES
    return Path(__file__).resolve().parents[3] / _DEFAULT_RULES


def build_audit_workflow() -> AuditWorkflow:
    """Create the workflow used by the desktop window."""
    return AuditWorkflow(
        WorkflowPorts(
            read_model=_translated(parse_erwin_repository),
            read_thesaurus=_translated(read_thesaurus),
            read_specification=_translated(read_entity_specification),
            read_rules=_translated(load_rule_catalog),
            digest=_translated(sha256_of),
            write_excel=_translated(write_excel_report),
            write_pdf=_translated(write_pdf_report),
            now=lambda: datetime.now().astimezone(),
        )
    )
