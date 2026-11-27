"""Check that a name is composed only of approved thesaurus terms."""

from data_model_auditor.domain.audit_scope import AuditScope, ScopedColumn
from data_model_auditor.domain.reference_catalog import ThesaurusCatalog, ThesaurusEntry
from data_model_auditor.domain.rule_catalog import AuditRule, RuleConfigurationError
from data_model_auditor.domain.validation import RuleContext, ValidationFinding

_AUDITED = "audited"


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
        if rule is None or not rule.enabled:
            return ()
        physical_separator = _separator(rule, "physical_separator")
        logical_separator = _separator(rule, "logical_separator")
        physical_current, physical_deprecated = _vocabulary(
            self._thesaurus.entries,
            current="mnemonic",
            deprecated="deprecated_mnemonic",
        )
        logical_current, logical_deprecated = _vocabulary(
            self._thesaurus.entries,
            current="term",
            deprecated="deprecated_term",
        )
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            findings.extend(
                _check_name(
                    rule,
                    context,
                    scope.subject_area.name,
                    table.physical_name,
                    table.physical_name,
                    "",
                    "",
                    physical_separator,
                    physical_current,
                    physical_deprecated,
                    "mnemônico",
                )
            )
            findings.extend(
                _check_name(
                    rule,
                    context,
                    scope.subject_area.name,
                    table.physical_name,
                    table.logical_name,
                    "",
                    "",
                    logical_separator,
                    logical_current,
                    logical_deprecated,
                    "termo",
                )
            )
        for scoped in scope.columns:
            if scoped.role != _AUDITED:
                continue
            table_name = _table_name(scope, scoped)
            findings.extend(
                _check_name(
                    rule,
                    context,
                    scope.subject_area.name,
                    table_name,
                    scoped.column.physical_name,
                    scoped.column.physical_name,
                    scoped.column.logical_name,
                    physical_separator,
                    physical_current,
                    physical_deprecated,
                    "mnemônico",
                )
            )
            findings.extend(
                _check_name(
                    rule,
                    context,
                    scope.subject_area.name,
                    table_name,
                    scoped.column.logical_name,
                    scoped.column.physical_name,
                    scoped.column.logical_name,
                    logical_separator,
                    logical_current,
                    logical_deprecated,
                    "termo",
                )
            )
        return tuple(findings)


def _separator(rule: AuditRule, name: str) -> str:
    for key, value in rule.parameters:
        if key == name and isinstance(value, str) and value != "":
            return value
    raise RuleConfigurationError(f"Rule {rule.code} requires parameter {name}.")


def _vocabulary(
    entries: tuple[ThesaurusEntry, ...],
    *,
    current: str,
    deprecated: str,
) -> tuple[dict[str, str], dict[str, str]]:
    approved: dict[str, str] = {}
    retired: dict[str, str] = {}
    for entry in entries:
        current_value = str(getattr(entry, current)).strip()
        retired_value = str(getattr(entry, deprecated)).strip()
        replacement = current_value or str(entry.term).strip()
        if current_value:
            approved[current_value.casefold()] = current_value
        if retired_value:
            retired.setdefault(retired_value.casefold(), replacement)
    return approved, retired


def _table_name(scope: AuditScope, scoped: ScopedColumn) -> str:
    for table in scope.tables:
        if table.origin_id == scoped.table_id:
            return table.physical_name
    return ""


def _check_name(
    rule: AuditRule,
    context: RuleContext,
    subject_area: str,
    table_name: str,
    name: str,
    physical_field_name: str,
    logical_field_name: str,
    separator: str,
    approved: dict[str, str],
    retired: dict[str, str],
    term_kind: str,
) -> tuple[ValidationFinding, ...]:
    if not name.strip():
        return (
            _finding(
                rule,
                context,
                subject_area,
                table_name,
                physical_field_name,
                logical_field_name,
                "O nome está vazio.",
                "A composição exige termos aprovados.",
                "Informe um nome composto por termos vigentes.",
            ),
        )
    findings: list[ValidationFinding] = []
    for token in name.split(separator):
        stripped = token.strip()
        if not stripped:
            findings.append(
                _finding(
                    rule,
                    context,
                    subject_area,
                    table_name,
                    physical_field_name,
                    logical_field_name,
                    f"O nome '{name}' tem um termo vazio.",
                    "Separadores consecutivos não formam um termo.",
                    "Remova o separador excedente.",
                )
            )
            continue
        key = stripped.casefold()
        if key in approved:
            continue
        if key in retired:
            replacement = retired[key]
            suggestion = (
                f"Substitua por '{replacement}'."
                if replacement
                else "Substitua pela forma vigente."
            )
            findings.append(
                _finding(
                    rule,
                    context,
                    subject_area,
                    table_name,
                    physical_field_name,
                    logical_field_name,
                    f"O {term_kind} '{stripped}' está preterido.",
                    "Somente a forma vigente compõe um nome válido.",
                    suggestion,
                )
            )
            continue
        findings.append(
            _finding(
                rule,
                context,
                subject_area,
                table_name,
                physical_field_name,
                logical_field_name,
                f"O {term_kind} '{stripped}' não está no thesaurus.",
                "O nome só é válido quando cada termo está aprovado.",
                f"Substitua '{stripped}' por um {term_kind} vigente.",
            )
        )
    return tuple(findings)


def _finding(
    rule: AuditRule,
    context: RuleContext,
    subject_area: str,
    table_name: str,
    physical_field_name: str,
    logical_field_name: str,
    message: str,
    justification: str,
    correction_suggestion: str,
) -> ValidationFinding:
    return ValidationFinding(
        rule_code=rule.code,
        severity=rule.severity,
        message=message,
        justification=justification,
        correction_suggestion=correction_suggestion,
        source=rule.normative_source,
        rule_version=context.rule_version,
        subject_area=subject_area,
        table_name=table_name,
        physical_field_name=physical_field_name,
        logical_field_name=logical_field_name,
        validation_type=rule.category.value,
        normative_page=rule.normative_page,
    )
