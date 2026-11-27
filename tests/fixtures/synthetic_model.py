"""Build small synthetic models and rules for validator tests."""

from dataclasses import replace

from data_model_auditor.domain.audit_scope import AuditScope, select_audit_scope
from data_model_auditor.domain.data_model import (
    KeyGroup,
    KeyMember,
    LogicalDataModel,
    ModelColumn,
    ModelRelationship,
    ModelTable,
    SubjectArea,
)
from data_model_auditor.domain.rule_catalog import (
    AuditRule,
    RequiredReference,
    RuleCategory,
    RuleParameter,
)
from data_model_auditor.domain.severity import Severity
from data_model_auditor.domain.validation import RuleContext

CONTEXT = RuleContext(rule_version="1.0")


def rule(
    code: str,
    category: RuleCategory,
    parameters: dict[str, RuleParameter] | None = None,
    *,
    reference: RequiredReference = RequiredReference.NONE,
    enabled: bool = True,
) -> AuditRule:
    """A rule with a synthetic source."""
    return AuditRule(
        code=code,
        name=code,
        category=category,
        enabled=enabled,
        severity=Severity.MEDIUM,
        normative_source="synthetic test rule",
        required_reference=reference,
        parameters=tuple(sorted((parameters or {}).items())),
    )


def column(
    origin_id: str,
    physical_name: str,
    physical_type: str = "INT",
    *,
    nullable: bool | None = False,
    definition: str = "Synthetic description",
    default_value: str = "",
    parent_attribute_id: str = "",
) -> ModelColumn:
    """A column with a logical name derived from the physical one."""
    return ModelColumn(
        origin_id=origin_id,
        logical_name=physical_name.replace("_", " ").title(),
        physical_name=physical_name,
        logical_data_type=physical_type,
        physical_data_type=physical_type,
        nullable=nullable,
        definition=definition,
        default_value=default_value,
        parent_attribute_id=parent_attribute_id,
    )


def key(
    origin_id: str,
    key_type: str,
    attribute_ids: tuple[str, ...],
    *,
    is_unique: bool | None = None,
) -> KeyGroup:
    """A key group whose members point to ``attribute_ids``."""
    return KeyGroup(
        origin_id=origin_id,
        name=origin_id,
        physical_name=origin_id.upper(),
        key_group_type=key_type,
        members=tuple(
            KeyMember(f"{origin_id}-{index}", attribute_id, attribute_id, attribute_id)
            for index, attribute_id in enumerate(attribute_ids)
        ),
        is_unique=is_unique,
    )


def table(
    origin_id: str,
    physical_name: str,
    columns: tuple[ModelColumn, ...],
    keys: tuple[KeyGroup, ...] = (),
    *,
    definition: str = "Synthetic table",
) -> ModelTable:
    """A table with the given columns and key groups."""
    return ModelTable(
        origin_id=origin_id,
        logical_name=physical_name.title(),
        physical_name=physical_name,
        definition=definition,
        columns=columns,
        key_groups=keys,
    )


def customer_order_model() -> LogicalDataModel:
    """CUSTOMER is the parent of ORDER. Only ORDER is in the Billing area."""
    customer = table(
        "customer",
        "CUSTOMER",
        (column("c1", "CD_CUSTOMER", "INT"), column("c2", "NM_CUSTOMER", "VARCHAR(50)")),
        (key("pk_customer", "PK", ("c1",)),),
    )
    order = table(
        "order",
        "ORDER",
        (
            column("o1", "CD_ORDER", "INT"),
            column("o2", "CD_CUSTOMER", "INT", parent_attribute_id="c1"),
        ),
        (key("pk_order", "PK", ("o1",)), key("if_order", "IF1", ("o2",))),
    )
    return LogicalDataModel(
        name="Synthetic",
        origin_id="model",
        target_server="172",
        dbms_major_version="15",
        dbms_minor_version="0",
        subject_areas=(
            SubjectArea("all", "All", "", ("customer", "order")),
            SubjectArea("billing", "Billing", "", ("order",)),
        ),
        tables=(customer, order),
        relationships=(ModelRelationship("r1", "places", "customer", "order", "pk_customer"),),
    )


def scope_of(
    tables: tuple[ModelTable, ...],
    *,
    area: str = "All",
) -> AuditScope:
    """Scope every table in a one-area model built from ``tables``."""
    model = LogicalDataModel(
        name="Synthetic",
        origin_id="model",
        target_server="172",
        dbms_major_version="15",
        dbms_minor_version="0",
        subject_areas=(SubjectArea("all", area, "", tuple(item.origin_id for item in tables)),),
        tables=tables,
        relationships=(),
    )
    return select_audit_scope(model, area)


def with_tables(model: LogicalDataModel, tables: tuple[ModelTable, ...]) -> LogicalDataModel:
    """Copy ``model`` with other tables."""
    return replace(model, tables=tables)
