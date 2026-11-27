"""Tests for the external YAML rule catalog."""

from pathlib import Path

import pytest

from data_model_auditor.domain.rule_catalog import (
    MissingRuleReferenceError,
    RequiredReference,
    RuleCategory,
    RuleConfigurationError,
    plan_rule_run,
    set_category_enabled,
)
from data_model_auditor.domain.severity import Severity
from data_model_auditor.infrastructure.rules.yaml_rules import (
    load_rule_catalog,
    parse_rule_catalog,
)

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = _ROOT / "rules" / "default_rules.yaml"

_MINIMAL = """
version: "9"
rules:
  - code: NAME-001
    name: Names
    category: naming
    enabled: true
    severity: low
    normative_source: "MVP V1 specification, section 10.1"
    required_reference: thesaurus
    parameters: {}
"""


def test_default_catalog_keeps_version_severity_and_source() -> None:
    catalog = load_rule_catalog(_DEFAULT)
    naming = next(rule for rule in catalog.rules if rule.code == "NAME-001")
    primary_key = next(rule for rule in catalog.rules if rule.code == "PK-001")

    assert catalog.version == "1.0"
    assert len(catalog.rules) == 10
    assert naming.severity is Severity.HIGH
    assert naming.required_reference is RequiredReference.THESAURUS
    assert naming.normative_source.startswith("MVP V1 specification")
    assert primary_key.parameters == (("require_primary_key", True),)
    assert all("pdf" not in rule.normative_source.casefold() for rule in catalog.rules)


def test_invalid_yaml_is_a_configuration_error() -> None:
    with pytest.raises(RuleConfigurationError, match="not valid YAML"):
        parse_rule_catalog("version: [\n")


def test_unknown_severity_is_a_configuration_error() -> None:
    text = _MINIMAL.replace("severity: low", "severity: urgent")
    with pytest.raises(RuleConfigurationError, match="expected structure"):
        parse_rule_catalog(text)


def test_blank_source_is_a_configuration_error() -> None:
    text = _MINIMAL.replace(
        'normative_source: "MVP V1 specification, section 10.1"',
        'normative_source: "  "',
    )
    with pytest.raises(RuleConfigurationError, match="expected structure"):
        parse_rule_catalog(text)


def test_duplicate_code_is_a_configuration_error() -> None:
    text = _MINIMAL.replace("rules:", "rules:\n" + _MINIMAL.split("rules:", 1)[1])
    with pytest.raises(RuleConfigurationError, match="unique"):
        parse_rule_catalog(text)


def test_missing_file_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(RuleConfigurationError, match="not found"):
        load_rule_catalog(tmp_path / "missing.yaml")


def test_another_file_can_be_selected(tmp_path: Path) -> None:
    path = tmp_path / "custom.yaml"
    path.write_text(_MINIMAL, encoding="utf-8")
    catalog = load_rule_catalog(path)
    assert catalog.version == "9"
    assert catalog.rules[0].severity is Severity.LOW


def test_disabled_category_is_skipped_and_recorded() -> None:
    catalog = set_category_enabled(
        parse_rule_catalog(_MINIMAL),
        RuleCategory.NAMING,
        enabled=False,
    )
    plan = plan_rule_run(catalog, frozenset())
    assert plan.rules == ()
    assert plan.skipped[0].code == "NAME-001"
    assert plan.skipped[0].reason == "disabled"


def test_enabled_rule_without_its_reference_blocks_the_run() -> None:
    catalog = parse_rule_catalog(_MINIMAL)
    with pytest.raises(MissingRuleReferenceError, match="NAME-001") as caught:
        plan_rule_run(catalog, frozenset())
    assert caught.value.reference is RequiredReference.THESAURUS


def test_enabled_rule_runs_when_the_reference_is_present() -> None:
    catalog = parse_rule_catalog(_MINIMAL)
    plan = plan_rule_run(catalog, frozenset({RequiredReference.THESAURUS}))
    assert [rule.code for rule in plan.rules] == ["NAME-001"]
    assert plan.skipped == ()
    assert plan.version == "9"
