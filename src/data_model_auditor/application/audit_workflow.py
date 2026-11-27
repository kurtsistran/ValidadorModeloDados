"""Desktop use cases: load inputs, run the audit, and export reports.

Readers and writers are injected so this module does not depend on file
formats, PySide6, or any library that parses documents.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from data_model_auditor.application.audit_service import (
    AuditRequest,
    AuditResult,
    SourceFile,
    run_audit,
)
from data_model_auditor.application.report_content import ReportContent, build_report_content
from data_model_auditor.application.validator_registry import AuditReferences
from data_model_auditor.domain.data_model import LogicalDataModel
from data_model_auditor.domain.reference_catalog import EntitySpecification, ThesaurusCatalog
from data_model_auditor.domain.rule_catalog import RuleCatalog, set_rule_enabled


class InputFileError(Exception):
    """An input file could not be read. The message is safe to show."""


@dataclass(frozen=True)
class WorkflowPorts:
    """Adapters supplied by the bootstrap."""

    read_model: Callable[[Path], LogicalDataModel]
    read_thesaurus: Callable[[Path], ThesaurusCatalog]
    read_specification: Callable[[Path], EntitySpecification]
    read_rules: Callable[[Path], RuleCatalog]
    digest: Callable[[Path], str]
    write_excel: Callable[[ReportContent, Path], None]
    write_pdf: Callable[[ReportContent, Path], None]
    now: Callable[[], datetime]


@dataclass(frozen=True)
class LoadedModel:
    """A parsed export and the identity of its file."""

    model: LogicalDataModel
    source: SourceFile


@dataclass(frozen=True)
class AuditSession:
    """Everything chosen in the window for one run."""

    loaded: LoadedModel
    rules_path: Path
    request: AuditRequest
    thesaurus_path: Path | None = None
    specification_path: Path | None = None
    disabled_rules: frozenset[str] = field(default_factory=frozenset)


class AuditWorkflow:
    """Coordinate one local audit without a server or a database."""

    def __init__(self, ports: WorkflowPorts) -> None:
        self._ports = ports

    def load_model(self, path: Path) -> LoadedModel:
        """Parse the Erwin export and fingerprint it."""
        model = self._ports.read_model(path)
        return LoadedModel(model, self._source("XML Erwin", path))

    def load_rules(self, path: Path) -> RuleCatalog:
        """Read the YAML rule file."""
        return self._ports.read_rules(path)

    def run(self, session: AuditSession) -> AuditResult:
        """Read the references, apply the rule choices, and audit the scope."""
        catalog = self._ports.read_rules(session.rules_path)
        for code in sorted(session.disabled_rules):
            catalog = set_rule_enabled(catalog, code, enabled=False)
        sources = [session.loaded.source, self._source("Regras YAML", session.rules_path)]
        thesaurus = None
        if session.thesaurus_path is not None:
            thesaurus = self._ports.read_thesaurus(session.thesaurus_path)
            sources.append(self._source("Thesaurus", session.thesaurus_path))
        specification = None
        if session.specification_path is not None:
            specification = self._ports.read_specification(session.specification_path)
            sources.append(self._source("SM077", session.specification_path))
        return run_audit(
            session.loaded.model,
            catalog,
            AuditReferences(thesaurus=thesaurus, specification=specification),
            session.request,
            tuple(sources),
            self._ports.now(),
        )

    def export_excel(self, result: AuditResult, path: Path) -> None:
        """Write the XLSX report. The audited files are not touched."""
        self._ports.write_excel(build_report_content(result), path)

    def export_pdf(self, result: AuditResult, path: Path) -> None:
        """Write the PDF report. The audited files are not touched."""
        self._ports.write_pdf(build_report_content(result), path)

    def _source(self, role: str, path: Path) -> SourceFile:
        return SourceFile(role=role, name=path.name, sha256=self._ports.digest(path))
