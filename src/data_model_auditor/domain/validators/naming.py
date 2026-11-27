"""Check that a name is composed only of approved thesaurus terms."""

from dataclasses import dataclass

from data_model_auditor.domain.audit_scope import AUDITED, AuditScope
from data_model_auditor.domain.reference_catalog import ThesaurusCatalog, ThesaurusEntry
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    FindingTarget,
    Violation,
    build_finding,
    column_target,
    is_active,
    table_target,
    text_parameter,
)


@dataclass(frozen=True)
class _Vocabulary:
    """Current and deprecated forms for one kind of name."""

    separator: str
    approved: frozenset[str]
    retired: dict[str, str]
    term_kind: str


class NamingValidator:
    """Validate physical and logical names against the current thesaurus."""

    def __init__(self, rule: AuditRule | None, thesaurus: ThesaurusCatalog) -> None:
        self._rule = rule
        self._thesaurus = thesaurus

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return one finding per token that is missing or deprecated."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        physical = _vocabulary(
            self._thesaurus.entries,
            text_parameter(rule, "physical_separator"),
            current="mnemonic",
            deprecated="deprecated_mnemonic",
            term_kind="mnemônico",
        )
        logical = _vocabulary(
            self._thesaurus.entries,
            text_parameter(rule, "logical_separator"),
            current="term",
            deprecated="deprecated_term",
            term_kind="termo",
        )
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            target = table_target(scope, table)
            findings.extend(_check(rule, context, target, table.physical_name, physical))
            findings.extend(_check(rule, context, target, table.logical_name, logical))
        for scoped in scope.columns:
            if scoped.role != AUDITED:
                continue
            target = column_target(scope, scoped)
            column = scoped.column
            findings.extend(_check(rule, context, target, column.physical_name, physical))
            findings.extend(_check(rule, context, target, column.logical_name, logical))
        return tuple(findings)


def _vocabulary(
    entries: tuple[ThesaurusEntry, ...],
    separator: str,
    *,
    current: str,
    deprecated: str,
    term_kind: str,
) -> _Vocabulary:
    approved: set[str] = set()
    retired: dict[str, str] = {}
    for entry in entries:
        current_value = str(getattr(entry, current)).strip()
        retired_value = str(getattr(entry, deprecated)).strip()
        if current_value:
            approved.add(current_value.casefold())
        if retired_value:
            retired.setdefault(retired_value.casefold(), current_value or entry.term.strip())
    return _Vocabulary(separator, frozenset(approved), retired, term_kind)


def _check(
    rule: AuditRule,
    context: RuleContext,
    target: FindingTarget,
    name: str,
    vocabulary: _Vocabulary,
) -> tuple[ValidationFinding, ...]:
    if not name.strip():
        empty = Violation(
            "O nome está vazio.",
            "A composição exige termos aprovados.",
            "Informe um nome composto por termos vigentes.",
        )
        return (build_finding(rule, context, target, empty),)
    findings: list[ValidationFinding] = []
    for token in name.split(vocabulary.separator):
        violation = _token_violation(name, token.strip(), vocabulary)
        if violation is not None:
            findings.append(build_finding(rule, context, target, violation))
    return tuple(findings)


def _token_violation(name: str, token: str, vocabulary: _Vocabulary) -> Violation | None:
    kind = vocabulary.term_kind
    if not token:
        return Violation(
            f"O nome '{name}' tem um termo vazio.",
            "Separadores consecutivos não formam um termo.",
            "Remova o separador excedente.",
        )
    key = token.casefold()
    if key in vocabulary.approved:
        return None
    if key in vocabulary.retired:
        replacement = vocabulary.retired[key]
        suggestion = (
            f"Substitua por '{replacement}'." if replacement else "Substitua pela forma vigente."
        )
        return Violation(
            f"O {kind} '{token}' está preterido.",
            "Somente a forma vigente compõe um nome válido.",
            suggestion,
        )
    return Violation(
        f"O {kind} '{token}' não está no thesaurus.",
        "O nome só é válido quando cada termo está aprovado.",
        f"Substitua '{token}' por um {kind} vigente.",
    )
