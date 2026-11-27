"""Tests for the shared domain contracts."""

from data_model_auditor.domain.role import Role
from data_model_auditor.domain.severity import Severity
from data_model_auditor.domain.validation import RuleContext, ValidationFinding


def test_severity_and_role_values_match_the_specification() -> None:
    """The contracts use the severities and profiles required by the product."""
    assert [item.value for item in Severity] == ["critical", "high", "medium", "low", "info"]
    assert [item.value for item in Role] == ["administrator", "analyst", "viewer"]


def test_validation_finding_keeps_the_rule_trace() -> None:
    """A finding carries the rule identity, severity and guidance."""
    finding = ValidationFinding(
        rule_code="NAME-001",
        severity=Severity.HIGH,
        message="The physical name is not allowed.",
        justification="The term is absent from the approved list.",
        correction_suggestion="Use an approved term.",
        source="naming-sheet:1",
        rule_version="1",
    )

    assert finding.rule_version == RuleContext(rule_version="1").rule_version
    assert finding.severity is Severity.HIGH
