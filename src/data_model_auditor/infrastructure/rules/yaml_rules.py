"""Load a YAML rule file into the domain catalog."""

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from data_model_auditor.domain.rule_catalog import (
    AuditRule,
    RequiredReference,
    RuleCatalog,
    RuleCategory,
    RuleConfigurationError,
    RuleParameter,
)
from data_model_auditor.domain.severity import Severity

_SCALAR = (str, int, bool)


class _RuleEntry(BaseModel):
    """One rule object accepted from the YAML file."""

    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    category: RuleCategory
    enabled: bool
    severity: Severity
    normative_source: str
    required_reference: RequiredReference
    parameters: dict[str, RuleParameter] = Field(default_factory=dict)
    normative_page: int | None = None

    @field_validator("code", "name", "normative_source")
    @classmethod
    def _reject_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("parameters")
    @classmethod
    def _reject_nested_parameters(
        cls,
        value: dict[str, RuleParameter],
    ) -> dict[str, RuleParameter]:
        for name, parameter in value.items():
            if not isinstance(parameter, _SCALAR) or isinstance(parameter, float):
                raise ValueError(f"{name} must be text, an integer, or a boolean")
            if isinstance(parameter, str) and parameter == "":
                raise ValueError(f"{name} must not be blank")
        return value

    @field_validator("normative_page")
    @classmethod
    def _reject_non_positive_page(cls, value: int | None) -> int | None:
        if value is not None and value < 1:
            raise ValueError("must be a positive page number")
        return value


class _RuleFile(BaseModel):
    """Root object of a rule file."""

    model_config = ConfigDict(extra="forbid")

    version: str
    rules: list[_RuleEntry]

    @field_validator("version")
    @classmethod
    def _reject_blank_version(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


def load_rule_catalog(path: Path) -> RuleCatalog:
    """Read ``path`` and reject a file that does not match the rule contract."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuleConfigurationError(f"Rule file not found: {path.name}") from exc
    return parse_rule_catalog(text)


def parse_rule_catalog(text: str) -> RuleCatalog:
    """Parse YAML text. Callers that already read the file use this directly."""
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise RuleConfigurationError("Rule file is not valid YAML.") from exc
    if not isinstance(loaded, dict):
        raise RuleConfigurationError("Rule file must contain a mapping.")
    try:
        document = _RuleFile.model_validate(loaded)
    except ValidationError as exc:
        raise RuleConfigurationError("Rule file does not match the expected structure.") from exc
    codes = [rule.code for rule in document.rules]
    if len(codes) != len(set(codes)):
        raise RuleConfigurationError("Rule codes must be unique.")
    return RuleCatalog(
        version=document.version,
        rules=tuple(_to_rule(entry) for entry in document.rules),
    )


def _to_rule(entry: _RuleEntry) -> AuditRule:
    parameters = tuple(sorted(entry.parameters.items()))
    return AuditRule(
        code=entry.code,
        name=entry.name,
        category=entry.category,
        enabled=entry.enabled,
        severity=entry.severity,
        normative_source=entry.normative_source,
        required_reference=entry.required_reference,
        parameters=parameters,
        normative_page=entry.normative_page,
    )
