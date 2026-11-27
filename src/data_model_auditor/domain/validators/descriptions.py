"""Description checks on tables and columns."""

from data_model_auditor.domain.audit_scope import AUDITED, AuditScope
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    Violation,
    build_finding,
    column_target,
    is_active,
    parameter,
    table_target,
)


class DescriptionValidator:
    """Report tables and columns without a description in the model."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return a finding for each empty or too-short description."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        minimum = parameter(rule, "min_length")
        min_length = minimum if isinstance(minimum, int) and not isinstance(minimum, bool) else 0
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            violation = _violation("tabela", table.physical_name, table.definition, min_length)
            if violation is not None:
                findings.append(build_finding(rule, context, table_target(scope, table), violation))
        for scoped in scope.columns:
            if scoped.role != AUDITED:
                continue
            column = scoped.column
            violation = _violation("coluna", column.physical_name, column.definition, min_length)
            if violation is not None:
                findings.append(
                    build_finding(rule, context, column_target(scope, scoped), violation)
                )
        return tuple(findings)


def _violation(kind: str, name: str, definition: str, min_length: int) -> Violation | None:
    text = " ".join(definition.split())
    if not text:
        return Violation(
            f"A {kind} '{name}' não tem descrição.",
            "Todo objeto auditado precisa de descrição.",
            f"Descreva a finalidade da {kind}.",
        )
    if min_length and len(text) < min_length:
        return Violation(
            f"A descrição da {kind} '{name}' tem menos de {min_length} caracteres.",
            "A regra define um tamanho mínimo para a descrição.",
            "Complete a descrição com a finalidade do objeto.",
        )
    return None
