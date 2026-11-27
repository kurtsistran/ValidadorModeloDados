"""Standard result produced by a deterministic validator."""

from dataclasses import dataclass

from data_model_auditor.domain.severity import Severity


@dataclass(frozen=True)
class RuleContext:
    """Version of the rules supplied to a validation run.

    Normative rule content is not stored here. A rule stays inactive until a
    person approves it.
    """

    rule_version: str


@dataclass(frozen=True)
class ValidationFinding:
    """One inconsistency reported by a validator."""

    rule_code: str
    severity: Severity
    message: str
    justification: str
    correction_suggestion: str
    source: str
    rule_version: str
    subject_area: str = ""
    table_name: str = ""
    physical_field_name: str = ""
    logical_field_name: str = ""
    validation_type: str = ""
    normative_page: int | None = None
