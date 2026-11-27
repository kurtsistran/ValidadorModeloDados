"""Tests for the validation engine."""

from data_model_auditor.application.validation_engine import ValidationEngine
from data_model_auditor.domain.severity import Severity
from data_model_auditor.domain.validation import RuleContext, ValidationFinding


class _RecordingValidator:
    def __init__(self, code: str) -> None:
        self.code = code

    def validate(
        self,
        subject: str,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        return (
            ValidationFinding(
                rule_code=self.code,
                severity=Severity.INFO,
                message=subject,
                justification="Recorded by the test validator.",
                correction_suggestion="",
                source="test",
                rule_version=context.rule_version,
            ),
        )


def test_engine_runs_validators_in_order() -> None:
    """A new validator is added by passing it to the engine, not by editing another."""
    engine = ValidationEngine(
        (_RecordingValidator("A"), _RecordingValidator("B")),
    )

    findings = engine.run("table", RuleContext(rule_version="3"))

    assert [finding.rule_code for finding in findings] == ["A", "B"]
    assert findings[0].rule_version == "3"


def test_engine_without_validators_returns_no_findings() -> None:
    """The engine does not invent findings when no validator is registered."""
    engine: ValidationEngine[str] = ValidationEngine(())

    assert engine.run("table", RuleContext(rule_version="1")) == ()
