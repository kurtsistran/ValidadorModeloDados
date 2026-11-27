"""Run the audit service with the default YAML and a synthetic model."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from data_model_auditor.application.audit_service import AuditRequest, run_audit
from data_model_auditor.application.validator_registry import (
    AuditReferences,
    supported_rule_codes,
)
from data_model_auditor.domain.audit_scope import SubjectAreaRequiredError
from data_model_auditor.domain.reference_catalog import (
    NameClass,
    ThesaurusCatalog,
    ThesaurusEntry,
)
from data_model_auditor.domain.rule_catalog import (
    MissingRuleReferenceError,
    set_rule_enabled,
)
from data_model_auditor.domain.target_database import TargetDatabase
from data_model_auditor.infrastructure.rules.yaml_rules import load_rule_catalog
from fixtures.synthetic_model import customer_order_model

_RULES = Path(__file__).resolve().parents[2] / "rules" / "default_rules.yaml"
_NOW = datetime(2026, 1, 1, tzinfo=UTC)
_THESAURUS = ThesaurusCatalog(
    entries=(
        ThesaurusEntry("Código", "CD", "", ""),
        ThesaurusEntry("Customer", "CUSTOMER", "", ""),
        ThesaurusEntry("Order", "ORDER", "", ""),
    ),
    name_classes=(NameClass("1", "Código", "CD", "C", ""),),
)


def _request(area: str = "All") -> AuditRequest:
    return AuditRequest(subject_area=area, target_database=TargetDatabase.SQLSERVER)


def test_every_default_rule_has_a_validator() -> None:
    codes = {rule.code for rule in load_rule_catalog(_RULES).rules}
    assert codes <= supported_rule_codes()


def test_missing_sm077_blocks_until_the_rule_is_disabled() -> None:
    catalog = load_rule_catalog(_RULES)
    references = AuditReferences(thesaurus=_THESAURUS)
    with pytest.raises(MissingRuleReferenceError, match="DESC-002"):
        run_audit(customer_order_model(), catalog, references, _request(), (), _NOW)

    allowed = set_rule_enabled(catalog, "DESC-002", enabled=False)
    result = run_audit(customer_order_model(), allowed, references, _request(), (), _NOW)

    assert [item.code for item in result.plan.skipped] == ["DESC-002"]
    assert result.plan.version == "1.0"
    assert all(item.rule_version == "1.0" for item in result.findings)
    assert {item.subject_area for item in result.findings} == {"All"}


def test_run_requires_a_subject_area() -> None:
    catalog = load_rule_catalog(_RULES)
    with pytest.raises(SubjectAreaRequiredError):
        run_audit(
            customer_order_model(),
            catalog,
            AuditReferences(thesaurus=_THESAURUS),
            _request(" "),
            (),
            _NOW,
        )


def test_partial_scope_keeps_the_parent_as_a_structural_dependency() -> None:
    catalog = set_rule_enabled(load_rule_catalog(_RULES), "DESC-002", enabled=False)
    result = run_audit(
        customer_order_model(),
        catalog,
        AuditReferences(thesaurus=_THESAURUS),
        _request("Billing"),
        (),
        _NOW,
    )
    assert [table.physical_name for table in result.scope.tables] == ["ORDER"]
    assert [table.physical_name for table in result.scope.structural_tables] == ["CUSTOMER"]
    assert {item.table_name for item in result.findings} <= {"ORDER"}
