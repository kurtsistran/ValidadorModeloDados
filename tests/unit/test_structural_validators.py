"""Tests for table, key, index, type, and DEFAULT validators."""

from dataclasses import replace

import pytest

from data_model_auditor.domain.audit_scope import select_audit_scope
from data_model_auditor.domain.data_type import parse_physical_type
from data_model_auditor.domain.rule_catalog import RuleCategory, RuleConfigurationError
from data_model_auditor.domain.target_database import TargetDatabase, target_from_erwin
from data_model_auditor.domain.validators.data_types import (
    DataTypeValidator,
    DefaultValueValidator,
)
from data_model_auditor.domain.validators.indexes import IndexValidator
from data_model_auditor.domain.validators.keys import ForeignKeyValidator, PrimaryKeyValidator
from data_model_auditor.domain.validators.tables import TableStructureValidator
from fixtures.synthetic_model import (
    CONTEXT,
    column,
    customer_order_model,
    key,
    rule,
    scope_of,
    table,
    with_tables,
)

_TYPES = {
    "sqlserver_types": "INT,VARCHAR,DECIMAL,DATETIME",
    "length_required_types": "VARCHAR",
    "precision_scale_types": "DECIMAL",
}


def test_physical_type_text_is_split_without_nullability() -> None:
    parsed = parse_physical_type("decimal(11, 2) NOT NULL")
    assert parsed.base == "DECIMAL"
    assert parsed.arguments == ("11", "2")
    assert parsed.normalized() == "DECIMAL(11,2)"
    assert parse_physical_type("INT IDENTITY").normalized() == "INT"
    assert parse_physical_type("").base == ""


def test_erwin_target_code_is_not_guessed() -> None:
    assert target_from_erwin("172") is TargetDatabase.SQLSERVER
    assert target_from_erwin("170") is None


def test_table_without_columns_is_reported() -> None:
    scope = scope_of((table("t1", "EMPTY", ()),))
    findings = TableStructureValidator(rule("TABLE-001", RuleCategory.TABLE)).validate(
        scope, CONTEXT
    )
    assert [item.table_name for item in findings] == ["EMPTY"]


def test_missing_primary_key_is_reported_only_when_required() -> None:
    scope = scope_of((table("t1", "NO_KEY", (column("c1", "CD_X"),)),))
    required = rule("PK-001", RuleCategory.PRIMARY_KEY, {"require_primary_key": True})
    optional = rule("PK-001", RuleCategory.PRIMARY_KEY, {"require_primary_key": False})
    assert len(PrimaryKeyValidator(required).validate(scope, CONTEXT)) == 1
    assert PrimaryKeyValidator(optional).validate(scope, CONTEXT) == ()


def test_nullable_primary_key_column_is_reported() -> None:
    nullable = column("c1", "CD_X", nullable=True)
    scope = scope_of((table("t1", "T", (nullable,), (key("pk", "PK", ("c1",)),)),))
    findings = PrimaryKeyValidator(
        rule("PK-001", RuleCategory.PRIMARY_KEY, {"require_primary_key": True})
    ).validate(scope, CONTEXT)
    assert [item.physical_field_name for item in findings] == ["CD_X"]


def test_valid_foreign_key_has_no_finding() -> None:
    scope = select_audit_scope(customer_order_model(), "All")
    validator = ForeignKeyValidator(rule("FK-001", RuleCategory.FOREIGN_KEY))
    assert validator.validate(scope, CONTEXT) == ()


def test_foreign_key_type_mismatch_marks_the_structural_parent() -> None:
    model = customer_order_model()
    order = model.tables[1]
    changed = replace(order.columns[1], physical_data_type="BIGINT")
    order = replace(order, columns=(order.columns[0], changed))
    scope = select_audit_scope(with_tables(model, (model.tables[0], order)), "Billing")

    findings = ForeignKeyValidator(rule("FK-001", RuleCategory.FOREIGN_KEY)).validate(
        scope, CONTEXT
    )

    assert [table.physical_name for table in scope.structural_tables] == ["CUSTOMER"]
    assert len(findings) == 1
    assert "BIGINT" in findings[0].message
    assert "dependência estrutural" in findings[0].justification


def test_foreign_key_to_missing_column_is_reported() -> None:
    orphan = column("o2", "CD_GHOST", parent_attribute_id="missing")
    scope = scope_of((table("t1", "ORPHAN", (orphan,), (key("pk", "PK", ("o2",)),)),))
    findings = ForeignKeyValidator(rule("FK-001", RuleCategory.FOREIGN_KEY)).validate(
        scope, CONTEXT
    )
    assert "ausente" in findings[0].message


def test_data_type_rules_for_target_length_and_scale() -> None:
    columns = (
        column("c1", "CD_OK", "INT"),
        column("c2", "DS_NO_LENGTH", "VARCHAR()"),
        column("c3", "VR_BAD_SCALE", "DECIMAL(2,5)"),
        column("c4", "CD_ORACLE", "NUMBER(10)"),
        column("c5", "DS_EMPTY", ""),
    )
    scope = scope_of((table("t1", "T", columns),))
    findings = DataTypeValidator(
        rule("TYPE-001", RuleCategory.DATA_TYPE, _TYPES), TargetDatabase.SQLSERVER
    ).validate(scope, CONTEXT)
    assert [item.physical_field_name for item in findings] == [
        "DS_NO_LENGTH",
        "VR_BAD_SCALE",
        "CD_ORACLE",
        "DS_EMPTY",
    ]


def test_missing_type_list_for_the_target_is_a_configuration_error() -> None:
    scope = scope_of((table("t1", "T", (column("c1", "CD_X"),)),))
    validator = DataTypeValidator(
        rule("TYPE-001", RuleCategory.DATA_TYPE, _TYPES), TargetDatabase.ORACLE
    )
    with pytest.raises(RuleConfigurationError, match="oracle_types"):
        validator.validate(scope, CONTEXT)


def test_default_must_fit_the_type_and_nullability() -> None:
    columns = (
        column("c1", "VR_OK", "DECIMAL(5,2)", default_value="((0))"),
        column("c2", "VR_TEXT", "INT", default_value="('abc')"),
        column("c3", "CD_NULL", "INT", nullable=False, default_value="(NULL)"),
        column("c4", "DS_TEXT", "VARCHAR(10)", default_value="('abc')"),
    )
    scope = scope_of((table("t1", "T", columns),))
    findings = DefaultValueValidator(
        rule("DEF-001", RuleCategory.DEFAULT, {"numeric_types": "INT,DECIMAL"})
    ).validate(scope, CONTEXT)
    assert [item.physical_field_name for item in findings] == ["VR_TEXT", "CD_NULL"]


def test_index_composition_uniqueness_and_duplicates() -> None:
    columns = (column("c1", "CD_X"), column("c2", "CD_Y"))
    keys = (
        key("pk", "PK", ("c1",)),
        key("ie1", "IE1", ("c1",)),
        key("ie2", "IE2", ()),
        key("ak1", "AK1", ("c2",), is_unique=False),
        key("if1", "IF1", ("c1",)),
    )
    scope = scope_of((table("t1", "T", columns, keys),))
    findings = IndexValidator(rule("IDX-001", RuleCategory.INDEX)).validate(scope, CONTEXT)
    messages = [item.message for item in findings]
    assert len(messages) == 3
    assert any("IE1" in message and "PK" in message for message in messages)
    assert any("IE2" in message for message in messages)
    assert any("AK1" in message for message in messages)


def test_disabled_rules_produce_no_finding() -> None:
    scope = scope_of((table("t1", "EMPTY", ()),))
    disabled = rule("TABLE-001", RuleCategory.TABLE, enabled=False)
    assert TableStructureValidator(disabled).validate(scope, CONTEXT) == ()
    assert TableStructureValidator(None).validate(scope, CONTEXT) == ()
