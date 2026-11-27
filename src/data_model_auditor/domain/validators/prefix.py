"""Check that a column name starts or ends with an approved name class."""

from data_model_auditor.domain.audit_scope import AUDITED, AuditScope
from data_model_auditor.domain.reference_catalog import ThesaurusCatalog
from data_model_auditor.domain.rule_catalog import AuditRule, RuleConfigurationError
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    Violation,
    build_finding,
    column_target,
    is_active,
    text_parameter,
)

_POSITIONS = {"first": 0, "last": -1}


class PrefixValidator:
    """Compare the class token of each physical column name with the sheet."""

    def __init__(self, rule: AuditRule | None, thesaurus: ThesaurusCatalog) -> None:
        self._rule = rule
        self._classes = {
            item.abbreviation.strip().upper(): item.name
            for item in thesaurus.name_classes
            if item.abbreviation.strip()
        }

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return a finding for each audited column without an allowed class."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        separator = text_parameter(rule, "separator")
        position_name = text_parameter(rule, "position")
        if position_name not in _POSITIONS:
            raise RuleConfigurationError(f"Rule {rule.code} position must be first or last.")
        position = _POSITIONS[position_name]
        allowed = ", ".join(sorted(self._classes))
        findings: list[ValidationFinding] = []
        for scoped in scope.columns:
            if scoped.role != AUDITED:
                continue
            name = scoped.column.physical_name.strip()
            token = name.split(separator)[position].strip().upper() if name else ""
            if token in self._classes:
                continue
            violation = Violation(
                f"O nome '{name}' não usa uma classe de nome permitida.",
                f"O termo na posição '{position_name}' deve ser uma classe da planilha.",
                f"Use uma das classes: {allowed}.",
            )
            findings.append(build_finding(rule, context, column_target(scope, scoped), violation))
        return tuple(findings)
