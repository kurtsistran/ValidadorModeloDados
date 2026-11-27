"""Choose the subject area and the optional table and column scope."""

from dataclasses import dataclass

from data_model_auditor.domain.data_model import (
    LogicalDataModel,
    ModelColumn,
    ModelTable,
    SubjectArea,
)


class SubjectAreaSelectionError(Exception):
    """Base error for an audit scope that cannot be built."""


class NoSubjectAreaInModelError(SubjectAreaSelectionError):
    """The export has no subject area that can be selected."""


class SubjectAreaRequiredError(SubjectAreaSelectionError):
    """An audit was requested without a subject area."""


class SubjectAreaNotFoundError(SubjectAreaSelectionError):
    """The requested subject area is not in the model."""


class TableOutsideSubjectAreaError(SubjectAreaSelectionError):
    """A selected table does not belong to the chosen subject area."""


class ColumnOutsideSelectionError(SubjectAreaSelectionError):
    """A selected column is not part of the tables in scope."""


@dataclass(frozen=True)
class ScopedColumn:
    """A column included in the audit."""

    table_id: str
    column: ModelColumn
    role: str = "audited"


@dataclass(frozen=True)
class AuditScope:
    """Tables and columns that participate in one audit run."""

    subject_area: SubjectArea
    tables: tuple[ModelTable, ...]
    columns: tuple[ScopedColumn, ...]


def select_audit_scope(
    model: LogicalDataModel,
    subject_area_name: str,
    table_ids: tuple[str, ...] | None = None,
    column_ids: tuple[str, ...] | None = None,
) -> AuditScope:
    """Build the audit scope. A subject area is always required.

    An empty table selection means every table in the subject area. An empty
    column selection means every column of those tables.
    """
    if not model.subject_areas:
        raise NoSubjectAreaInModelError("The model has no identifiable subject area.")
    chosen_name = subject_area_name.strip()
    if not chosen_name:
        raise SubjectAreaRequiredError("Select a subject area before running the audit.")
    area = _find_area(model, chosen_name)
    tables = _tables_in_area(model, area)
    selected_tables = _selected_tables(tables, table_ids or ())
    selected_columns = _selected_columns(selected_tables, column_ids or ())
    return AuditScope(subject_area=area, tables=selected_tables, columns=selected_columns)


def _find_area(model: LogicalDataModel, name: str) -> SubjectArea:
    for area in model.subject_areas:
        if area.name.casefold() == name.casefold():
            return area
    raise SubjectAreaNotFoundError(f"Subject area was not found: {name}")


def _tables_in_area(model: LogicalDataModel, area: SubjectArea) -> tuple[ModelTable, ...]:
    if area.includes_all_entities:
        return model.tables
    members = set(area.member_ids)
    return tuple(table for table in model.tables if table.origin_id in members)


def _selected_tables(
    tables: tuple[ModelTable, ...],
    table_ids: tuple[str, ...],
) -> tuple[ModelTable, ...]:
    if not table_ids:
        return tables
    available = {table.origin_id: table for table in tables}
    chosen: list[ModelTable] = []
    for table_id in table_ids:
        table = available.get(table_id)
        if table is None:
            raise TableOutsideSubjectAreaError(
                "A selected table is outside the subject area."
            )
        chosen.append(table)
    return tuple(chosen)


def _selected_columns(
    tables: tuple[ModelTable, ...],
    column_ids: tuple[str, ...],
) -> tuple[ScopedColumn, ...]:
    scoped = [
        ScopedColumn(table_id=table.origin_id, column=column)
        for table in tables
        for column in table.columns
    ]
    if not column_ids:
        return tuple(scoped)
    wanted = set(column_ids)
    chosen = [item for item in scoped if item.column.origin_id in wanted]
    found = {item.column.origin_id for item in chosen}
    if found != wanted:
        raise ColumnOutsideSelectionError("A selected column is outside the current tables.")
    return tuple(chosen)
