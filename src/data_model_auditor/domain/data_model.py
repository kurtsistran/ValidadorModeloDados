"""Normalized model used by the audit, independent of the Erwin XML."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelColumn:
    """One attribute, with the names and types found in the export."""

    origin_id: str
    logical_name: str
    physical_name: str
    logical_data_type: str
    physical_data_type: str
    nullable: bool | None
    definition: str


@dataclass(frozen=True)
class KeyMember:
    """One attribute that belongs to a key group."""

    origin_id: str
    attribute_id: str
    name: str
    physical_name: str


@dataclass(frozen=True)
class KeyGroup:
    """A primary key, foreign key, alternate key, or index from the export."""

    origin_id: str
    name: str
    physical_name: str
    key_group_type: str
    members: tuple[KeyMember, ...]


@dataclass(frozen=True)
class ModelTable:
    """One entity and the columns and key groups it owns."""

    origin_id: str
    logical_name: str
    physical_name: str
    definition: str
    columns: tuple[ModelColumn, ...]
    key_groups: tuple[KeyGroup, ...]


@dataclass(frozen=True)
class ModelRelationship:
    """A relationship between two entities."""

    origin_id: str
    name: str
    parent_entity_id: str
    child_entity_id: str
    key_group_id: str


@dataclass(frozen=True)
class SubjectArea:
    """A named subject area and the entities attached to it."""

    origin_id: str
    name: str
    definition: str
    member_ids: tuple[str, ...]
    includes_all_entities: bool = False


@dataclass(frozen=True)
class LogicalDataModel:
    """The part of an Erwin export needed to choose an audit scope."""

    name: str
    origin_id: str
    target_server: str
    dbms_major_version: str
    dbms_minor_version: str
    subject_areas: tuple[SubjectArea, ...]
    tables: tuple[ModelTable, ...]
    relationships: tuple[ModelRelationship, ...]

    def table_by_id(self) -> dict[str, ModelTable]:
        """Index tables by the identifier used inside the export."""
        return {table.origin_id: table for table in self.tables}


def key_group_kind(key_group_type: str) -> str:
    """Classify a key-group code by its two-letter prefix.

    The export stores ``PK``, ``AKn``, ``IEn``, and ``IFn``. Any other code
    stays unclassified.
    """
    prefix = key_group_type[:2].upper()
    if prefix == "PK":
        return "primary"
    if prefix == "AK":
        return "alternate"
    if prefix == "IE":
        return "index"
    if prefix == "IF":
        return "foreign"
    return "unknown"
