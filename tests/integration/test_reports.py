"""Write Excel and PDF reports from a synthetic audit and read them back."""

from datetime import UTC, datetime
from pathlib import Path

import pymupdf  # type: ignore[import-untyped, unused-ignore]
import pytest
from openpyxl import load_workbook

from data_model_auditor.application.audit_service import AuditRequest, SourceFile, run_audit
from data_model_auditor.application.report_content import ReportContent, build_report_content
from data_model_auditor.application.validator_registry import AuditReferences
from data_model_auditor.domain.rule_catalog import set_rule_enabled
from data_model_auditor.domain.target_database import TargetDatabase
from data_model_auditor.infrastructure.reports.errors import ReportWriteError
from data_model_auditor.infrastructure.reports.excel_report import write_excel_report
from data_model_auditor.infrastructure.reports.pdf_report import write_pdf_report
from data_model_auditor.infrastructure.rules.yaml_rules import load_rule_catalog
from fixtures.synthetic_model import customer_order_model

_RULES = Path(__file__).resolve().parents[2] / "rules" / "default_rules.yaml"


def _content() -> ReportContent:
    catalog = load_rule_catalog(_RULES)
    for code in ("NAME-001", "PREF-001", "DESC-002"):
        catalog = set_rule_enabled(catalog, code, enabled=False)
    result = run_audit(
        customer_order_model(),
        catalog,
        AuditReferences(),
        AuditRequest("Billing", TargetDatabase.SQLSERVER),
        (SourceFile("XML Erwin", "model.xml", "ab" * 32),),
        datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )
    return build_report_content(result)


def test_report_content_lists_skipped_rules_and_structural_tables() -> None:
    content = _content()
    configuration = {row[0]: row for row in content.configuration.rows}
    assert configuration["Regra DESC-002"][1] == "Desativada explicitamente"
    assert configuration["Arquivo XML Erwin"][2].startswith("SHA-256 ")
    roles = {row[0]: row[2] for row in content.tables.rows}
    assert roles == {"ORDER": "Auditada", "CUSTOMER": "Dependência estrutural"}


def test_excel_report_has_the_five_sheets(tmp_path: Path) -> None:
    path = tmp_path / "audit.xlsx"
    write_excel_report(_content(), path)
    workbook = load_workbook(path, read_only=True)
    assert workbook.sheetnames == ["Resumo", "Inconsistências", "Tabelas", "Campos", "Configuração"]
    summary = workbook["Resumo"]
    values = {row[0]: row[1] for row in summary.iter_rows(min_row=2, values_only=True)}
    assert values["Subject Area"] == "Billing"
    workbook.close()


def test_pdf_report_contains_the_summary(tmp_path: Path) -> None:
    path = tmp_path / "audit.pdf"
    write_pdf_report(_content(), path)
    document = pymupdf.open(path)
    text = "".join(page.get_text() for page in document)
    document.close()
    assert "Resumo executivo" in text
    assert "Billing" in text
    assert "Página 1 de" in text


def test_writers_reject_the_wrong_extension(tmp_path: Path) -> None:
    with pytest.raises(ReportWriteError):
        write_excel_report(_content(), tmp_path / "audit.xls")
    with pytest.raises(ReportWriteError):
        write_pdf_report(_content(), tmp_path / "audit.txt")
