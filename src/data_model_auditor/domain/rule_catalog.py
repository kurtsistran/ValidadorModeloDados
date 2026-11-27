"""External validation rules selected for one audit run."""

from dataclasses import dataclass
from enum import StrEnum

from data_model_auditor.domain.severity import Severity


class RuleCategory(StrEnum):
    """Validation family that can be turned on or off together."""

    NAMING = "naming"
    PREFIX = "prefix"
    TABLE = "table"
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    DATA_TYPE = "data_type"
    DEFAULT = "default"
    INDEX = "index"
    DESCRIPTION = "description"


class RequiredReference(StrEnum):
    """Document an enabled rule needs before the audit may start."""

    NONE = "none"
    THESAURUS = "thesaurus"
    SM077 = "sm077"


RuleParameter = str | int | bool


class RuleConfigurationError(Exception):
    """The rule file or the selected references cannot start an audit."""


class MissingRuleReferenceError(RuleConfigurationError):
    """An enabled rule needs a reference that was not supplied."""

    def __init__(self, rule_code: str, reference: RequiredReference) -> None:
        self.rule_code = rule_code
        self.reference = reference
        super().__init__(
            f"Rule {rule_code} is enabled and requires {reference.value}."
        )


@dataclass(frozen=True)
class AuditRule:
    """One configurable rule. The file supplies the parameters, not Python code."""

    code: str
    name: str
    category: RuleCategory
    enabled: bool
    severity: Severity
    normative_source: str
    required_reference: RequiredReference
    parameters: tuple[tuple[str, RuleParameter], ...]
    normative_page: int | None = None


@dataclass(frozen=True)
class SkippedRule:
    """A rule left out of the run because it was explicitly disabled."""

    code: str
    category: RuleCategory
    reason: str


@dataclass(frozen=True)
class RuleCatalog:
    """The rules and the version identified for one execution."""

    version: str
    rules: tuple[AuditRule, ...]


@dataclass(frozen=True)
class RuleRunPlan:
    """Rules that will run, plus the disabled ones the report must show."""

    version: str
    rules: tuple[AuditRule, ...]
    skipped: tuple[SkippedRule, ...]


def set_category_enabled(
    catalog: RuleCatalog,
    category: RuleCategory,
    *,
    enabled: bool,
) -> RuleCatalog:
    """Return a catalog where every rule in ``category`` has the given state."""
    updated = tuple(
        _replace_enabled(rule, enabled) if rule.category is category else rule
        for rule in catalog.rules
    )
    return RuleCatalog(version=catalog.version, rules=updated)


def plan_rule_run(
    catalog: RuleCatalog,
    available_references: frozenset[RequiredReference],
) -> RuleRunPlan:
    """Keep enabled rules and record disabled ones.

    An enabled rule whose reference is missing stops the audit. Disabling that
    rule is the explicit choice that lets the run continue, and the skip is
    kept so the report can show it.
    """
    selected: list[AuditRule] = []
    skipped: list[SkippedRule] = []
    for rule in catalog.rules:
        if not rule.enabled:
            skipped.append(SkippedRule(rule.code, rule.category, "disabled"))
            continue
        if (
            rule.required_reference is not RequiredReference.NONE
            and rule.required_reference not in available_references
        ):
            raise MissingRuleReferenceError(rule.code, rule.required_reference)
        selected.append(rule)
    return RuleRunPlan(catalog.version, tuple(selected), tuple(skipped))


def _replace_enabled(rule: AuditRule, enabled: bool) -> AuditRule:
    return AuditRule(
        code=rule.code,
        name=rule.name,
        category=rule.category,
        enabled=enabled,
        severity=rule.severity,
        normative_source=rule.normative_source,
        required_reference=rule.required_reference,
        parameters=rule.parameters,
        normative_page=rule.normative_page,
    )
