"""Structural checks that apply to a whole table."""

from data_model_auditor.domain.audit_scope import AuditScope
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    Violation,
    build_finding,
    is_active,
    table_target,
)


class TableStructureValidator:
    """Report audited tables without a physical name or without columns."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return a finding for each incomplete audited table."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            target = table_target(scope, table)
            if not table.physical_name.strip():
                violation = Violation(
                    f"A tabela '{table.logical_name}' não tem nome físico.",
                    "A tabela precisa de nome físico para ser gerada.",
                    "Informe o nome físico da tabela.",
                )
                findings.append(build_finding(rule, context, target, violation))
            if not table.columns:
                violation = Violation(
                    f"A tabela '{table.physical_name}' não tem colunas.",
                    "Uma tabela precisa de ao menos uma coluna.",
                    "Inclua as colunas ou remova a tabela.",
                )
                findings.append(build_finding(rule, context, target, violation))
        return tuple(findings)
