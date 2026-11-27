"""Tests for the required subject-area scope."""

import pytest

from data_model_auditor.domain.audit_scope import (
    ColumnOutsideSelectionError,
    NoSubjectAreaInModelError,
    SubjectAreaNotFoundError,
    SubjectAreaRequiredError,
    TableOutsideSubjectAreaError,
    select_audit_scope,
)
from data_model_auditor.domain.data_model import (
    LogicalDataModel,
    ModelColumn,
    ModelTable,
    SubjectArea,
)


def _column(origin_id: str, name: str) -> ModelColumn:
    return ModelColumn(
        origin_id=origin_id,
        logical_name=name,
        physical_name=name,
        logical_data_type="CHAR",
        physical_data_type="CHAR(10)",
        nullable=True,
        definition="",
    )


def _table(origin_id: str, name: str, columns: tuple[ModelColumn, ...]) -> ModelTable:
    return ModelTable(
        origin_id=origin_id,
        logical_name=name,
        physical_name=name,
        definition="",
        columns=columns,
        key_groups=(),
    )


def _model() -> LogicalDataModel:
    customer_id = _column("c1", "CUSTOMER_ID")
    customer_name = _column("c2", "CUSTOMER_NAME")
    order_id = _column("o1", "ORDER_ID")
    return LogicalDataModel(
        name="Sample",
        origin_id="model",
        target_server="172",
        dbms_major_version="15",
        dbms_minor_version="0",
        subject_areas=(
            SubjectArea("sales", "Sales", "", ("customer",)),
            SubjectArea("billing", "Billing", "", ("order",)),
        ),
        tables=(
            _table("customer", "CUSTOMER", (customer_id, customer_name)),
            _table("order", "ORDER", (order_id,)),
        ),
        relationships=(),
    )


def test_subject_area_limits_tables() -> None:
    scope = select_audit_scope(_model(), "Sales")

    assert scope.subject_area.name == "Sales"
    assert [table.physical_name for table in scope.tables] == ["CUSTOMER"]
    assert [item.column.physical_name for item in scope.columns] == [
        "CUSTOMER_ID",
        "CUSTOMER_NAME",
    ]


def test_audit_requires_a_subject_area() -> None:
    with pytest.raises(SubjectAreaRequiredError):
        select_audit_scope(_model(), "  ")


def test_missing_subject_area_is_not_assumed() -> None:
    model = _model()
    empty = LogicalDataModel(
        name=model.name,
        origin_id=model.origin_id,
        target_server=model.target_server,
        dbms_major_version=model.dbms_major_version,
        dbms_minor_version=model.dbms_minor_version,
        subject_areas=(),
        tables=model.tables,
        relationships=(),
    )

    with pytest.raises(NoSubjectAreaInModelError):
        select_audit_scope(empty, "Sales")


def test_unknown_subject_area_is_rejected() -> None:
    with pytest.raises(SubjectAreaNotFoundError):
        select_audit_scope(_model(), "Archive")


def test_explicit_table_and_column_selection() -> None:
    scope = select_audit_scope(_model(), "sales", ("customer",), ("c2",))

    assert [table.origin_id for table in scope.tables] == ["customer"]
    assert [item.column.origin_id for item in scope.columns] == ["c2"]


def test_table_outside_the_area_is_rejected() -> None:
    with pytest.raises(TableOutsideSubjectAreaError):
        select_audit_scope(_model(), "Sales", ("order",), None)


def test_column_outside_the_selected_tables_is_rejected() -> None:
    with pytest.raises(ColumnOutsideSelectionError):
        select_audit_scope(_model(), "Sales", ("customer",), ("o1",))


def test_area_can_include_every_entity() -> None:
    model = _model()
    entire = LogicalDataModel(
        name=model.name,
        origin_id=model.origin_id,
        target_server=model.target_server,
        dbms_major_version=model.dbms_major_version,
        dbms_minor_version=model.dbms_minor_version,
        subject_areas=(SubjectArea("main", "Main", "", (), includes_all_entities=True),),
        tables=model.tables,
        relationships=(),
    )

    scope = select_audit_scope(entire, "Main")

    assert [table.origin_id for table in scope.tables] == ["customer", "order"]
