"""Index and alternate-key checks represented by Erwin key groups."""

from data_model_auditor.domain.audit_scope import AuditScope
from data_model_auditor.domain.data_model import KeyGroup, ModelTable, key_group_kind
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    Violation,
    build_finding,
    is_active,
    table_target,
)

_INDEX_KINDS = frozenset({"primary", "alternate", "index"})


class IndexValidator:
    """Check composition, duplication, and uniqueness of key groups."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return index findings for each audited table."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            for violation in _table_violations(table):
                findings.append(build_finding(rule, context, table_target(scope, table), violation))
        return tuple(findings)


def _table_violations(table: ModelTable) -> list[Violation]:
    violations: list[Violation] = []
    seen: dict[tuple[str, ...], KeyGroup] = {}
    for key in table.key_groups:
        kind = key_group_kind(key.key_group_type)
        if kind not in _INDEX_KINDS:
            continue
        if not key.members:
            violations.append(
                Violation(
                    f"O índice '{key.physical_name}' não tem colunas.",
                    "Um índice precisa de ao menos uma coluna.",
                    "Associe as colunas ou remova o índice.",
                )
            )
            continue
        if kind == "alternate" and key.is_unique is False:
            violations.append(
                Violation(
                    f"A chave alternativa '{key.physical_name}' não é única.",
                    "Chave alternativa identifica a linha e precisa ser única.",
                    "Marque a chave como única ou troque para índice comum.",
                )
            )
        composition = tuple(member.attribute_id for member in key.members)
        earlier = seen.get(composition)
        if earlier is not None:
            violations.append(
                Violation(
                    f"O índice '{key.physical_name}' repete as colunas de "
                    f"'{earlier.physical_name}'.",
                    "Dois índices com a mesma composição não trazem ganho.",
                    "Remova o índice duplicado.",
                )
            )
            continue
        seen[composition] = key
    return violations
