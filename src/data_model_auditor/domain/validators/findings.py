"""Shared helpers that turn a rule violation into a standard finding."""

from dataclasses import dataclass

from data_model_auditor.domain.audit_scope import AuditScope, ScopedColumn
from data_model_auditor.domain.data_model import ModelTable
from data_model_auditor.domain.rule_catalog import (
    AuditRule,
    RuleConfigurationError,
    RuleParameter,
)
from data_model_auditor.domain.validation import RuleContext, ValidationFinding


@dataclass(frozen=True)
class FindingTarget:
    """Where in the model a finding applies."""

    subject_area: str
    table_name: str
    physical_field_name: str = ""
    logical_field_name: str = ""


@dataclass(frozen=True)
class Violation:
    """What went wrong and how to fix it."""

    message: str
    justification: str
    correction_suggestion: str


def table_target(scope: AuditScope, table: ModelTable) -> FindingTarget:
    """Target a whole table."""
    return FindingTarget(scope.subject_area.name, table.physical_name)


def column_target(scope: AuditScope, scoped: ScopedColumn) -> FindingTarget:
    """Target one column of a table in scope."""
    return FindingTarget(
        subject_area=scope.subject_area.name,
        table_name=scope.table_name(scoped.table_id),
        physical_field_name=scoped.column.physical_name,
        logical_field_name=scoped.column.logical_name,
    )


def build_finding(
    rule: AuditRule,
    context: RuleContext,
    target: FindingTarget,
    violation: Violation,
) -> ValidationFinding:
    """Combine the rule trace, the location, and the violation."""
    return ValidationFinding(
        rule_code=rule.code,
        severity=rule.severity,
        message=violation.message,
        justification=violation.justification,
        correction_suggestion=violation.correction_suggestion,
        source=rule.normative_source,
        rule_version=context.rule_version,
        subject_area=target.subject_area,
        table_name=target.table_name,
        physical_field_name=target.physical_field_name,
        logical_field_name=target.logical_field_name,
        validation_type=rule.category.value,
        normative_page=rule.normative_page,
    )


def is_active(rule: AuditRule | None) -> bool:
    """A validator without an enabled rule produces no finding."""
    return rule is not None and rule.enabled


def parameter(rule: AuditRule, name: str) -> RuleParameter | None:
    """Return a rule parameter, or ``None`` when the YAML omits it."""
    for key, value in rule.parameters:
        if key == name:
            return value
    return None


def text_parameter(rule: AuditRule, name: str) -> str:
    """Return a required non-empty text parameter."""
    value = parameter(rule, name)
    if isinstance(value, str) and value != "":
        return value
    raise RuleConfigurationError(f"Rule {rule.code} requires parameter {name}.")


def list_parameter(rule: AuditRule, name: str) -> frozenset[str]:
    """Read a comma-separated parameter as upper-case values."""
    value = text_parameter(rule, name)
    return frozenset(item.strip().upper() for item in value.split(",") if item.strip())
