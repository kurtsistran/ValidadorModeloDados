"""Runs independent validators and collects their findings."""

from collections.abc import Sequence
from typing import Protocol

from data_model_auditor.domain.validation import RuleContext, ValidationFinding


class Validator[Subject](Protocol):
    """Contract implemented by every deterministic validator."""

    def validate(
        self,
        subject: Subject,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return the findings for ``subject``. An empty tuple means no finding."""
        ...


class ValidationEngine[Subject]:
    """Execute validators without knowing the interface or an AI provider."""

    def __init__(self, validators: Sequence[Validator[Subject]]) -> None:
        self._validators = tuple(validators)

    def run(
        self,
        subject: Subject,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Run every validator and keep the findings in validator order."""
        findings: list[ValidationFinding] = []
        for validator in self._validators:
            findings.extend(validator.validate(subject, context))
        return tuple(findings)
