"""Tests for thesaurus name composition."""

import pytest

from data_model_auditor.domain.audit_scope import AuditScope, ScopedColumn
from data_model_auditor.domain.data_model import ModelColumn, ModelTable, SubjectArea
from data_model_auditor.domain.reference_catalog import ThesaurusCatalog, ThesaurusEntry
from data_model_auditor.domain.rule_catalog import (
    AuditRule,
    RequiredReference,
    RuleCategory,
    RuleConfigurationError,
)
from data_model_auditor.domain.severity import Severity
from data_model_auditor.domain.validation import RuleContext
from data_model_auditor.domain.validators.naming import NamingValidator

_CONTEXT = RuleContext(rule_version="1.0")


def _rule(*, enabled: bool = True) -> AuditRule:
    return AuditRule(
        code="NAME-001",
        name="Composição por termos do thesaurus",
        category=RuleCategory.NAMING,
        enabled=enabled,
        severity=Severity.HIGH,
        normative_source="MVP V1 specification, section 10.1",
        required_reference=RequiredReference.THESAURUS,
        parameters=(
            ("logical_separator", " "),
            ("physical_separator", "_"),
        ),
    )


def _catalog() -> ThesaurusCatalog:
    return ThesaurusCatalog(
        entries=(
            ThesaurusEntry("Cliente", "CLIENTE", "", ""),
            ThesaurusEntry("Código", "CD", "Codigo", "COD"),
        ),
        name_classes=(),
    )


def _column(origin_id: str, logical_name: str, physical_name: str) -> ModelColumn:
    return ModelColumn(
        origin_id=origin_id,
        logical_name=logical_name,
        physical_name=physical_name,
        logical_data_type="CHAR",
        physical_data_type="CHAR(10)",
        nullable=True,
        definition="",
    )


def _scope(column: ModelColumn, *, role: str = "audited") -> AuditScope:
    table = ModelTable(
        origin_id="t1",
        logical_name="Cliente",
        physical_name="CLIENTE",
        definition="",
        columns=(column,),
        key_groups=(),
    )
    return AuditScope(
        subject_area=SubjectArea("a1", "Vendas", "", ("t1",)),
        tables=(table,),
        columns=(ScopedColumn("t1", column, role),),
    )


def test_approved_terms_pass() -> None:
    scope = _scope(_column("c1", "Código Cliente", "CD_CLIENTE"))
    findings = NamingValidator(_rule(), _catalog()).validate(scope, _CONTEXT)
    assert findings == ()


def test_unknown_token_is_reported_and_a_contained_term_does_not_pass() -> None:
    scope = _scope(_column("c1", "Código Cliente", "CDCLIENTE"))
    findings = NamingValidator(_rule(), _catalog()).validate(scope, _CONTEXT)
    physical = [item for item in findings if item.physical_field_name == "CDCLIENTE"]
    assert len(physical) == 1
    assert "CDCLIENTE" in physical[0].message
    assert physical[0].rule_code == "NAME-001"
    assert physical[0].severity is Severity.HIGH
    assert physical[0].subject_area == "Vendas"
    assert physical[0].table_name == "CLIENTE"
    assert physical[0].validation_type == "naming"


def test_unknown_part_is_reported_without_accepting_the_valid_part() -> None:
    scope = _scope(_column("c1", "Código Cliente", "CD_XPTO"))
    findings = NamingValidator(_rule(), _catalog()).validate(scope, _CONTEXT)
    assert [item.message for item in findings] == [
        "O mnemônico 'XPTO' não está no thesaurus."
    ]


def test_deprecated_mnemonic_suggests_the_current_one() -> None:
    scope = _scope(_column("c1", "Código Cliente", "COD_CLIENTE"))
    findings = NamingValidator(_rule(), _catalog()).validate(scope, _CONTEXT)
    assert findings[0].correction_suggestion == "Substitua por 'CD'."


def test_disabled_rule_reports_nothing() -> None:
    scope = _scope(_column("c1", "Outro", "XPTO"))
    findings = NamingValidator(_rule(enabled=False), _catalog()).validate(scope, _CONTEXT)
    assert findings == ()


def test_structural_column_is_not_audited() -> None:
    scope = _scope(_column("c1", "Outro", "XPTO"), role="structural_dependency")
    findings = NamingValidator(_rule(), _catalog()).validate(scope, _CONTEXT)
    assert findings == ()


def test_missing_separator_parameter_is_a_configuration_error() -> None:
    rule = AuditRule(
        code="NAME-001",
        name="Composição por termos do thesaurus",
        category=RuleCategory.NAMING,
        enabled=True,
        severity=Severity.HIGH,
        normative_source="MVP V1 specification, section 10.1",
        required_reference=RequiredReference.THESAURUS,
        parameters=(),
    )
    scope = _scope(_column("c1", "Cliente", "CLIENTE"))
    with pytest.raises(RuleConfigurationError, match="physical_separator"):
        NamingValidator(rule, _catalog()).validate(scope, _CONTEXT)
