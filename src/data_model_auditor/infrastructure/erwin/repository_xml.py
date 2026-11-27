"""Read an Erwin repository export into the normalized model.

Only element names confirmed in a real repository export are interpreted.
External entities and document types are rejected. Parsing does not validate
business rules.
"""

from pathlib import Path

from lxml import etree

from data_model_auditor.domain.data_model import (
    KeyGroup,
    KeyMember,
    LogicalDataModel,
    ModelColumn,
    ModelRelationship,
    ModelTable,
    SubjectArea,
)

_MAX_BYTES = 1024 * 1024 * 1024
_OBJECTS = {
    "Model",
    "Subject_Area",
    "Entity",
    "Attribute",
    "Key_Group",
    "Key_Group_Member",
    "Relationship",
}
_PROPS_OF = {
    "ModelProps": "Model",
    "Subject_AreaProps": "Subject_Area",
    "EntityProps": "Entity",
    "AttributeProps": "Attribute",
    "Key_GroupProps": "Key_Group",
    "Key_Group_MemberProps": "Key_Group_Member",
    "RelationshipProps": "Relationship",
}


class ErwinXmlError(Exception):
    """Raised when a repository export cannot be read safely."""


class _Node:
    """Mutable builder for one object while the export is streamed."""

    def __init__(self, kind: str, origin_id: str) -> None:
        self.kind = kind
        self.origin_id = origin_id
        self.props: dict[str, str] = {}
        self.attributes: list[_Node] = []
        self.keys: list[_Node] = []
        self.members: list[_Node] = []
        self.member_refs: list[str] = []


def parse_erwin_repository(path: Path) -> LogicalDataModel:
    """Parse a repository-format export without loading the whole tree."""
    if not path.is_file():
        raise ErwinXmlError(f"File not found: {path.name}")
    if path.suffix.lower() != ".xml":
        raise ErwinXmlError("The Erwin export must be an XML file.")
    if path.stat().st_size > _MAX_BYTES:
        raise ErwinXmlError("The XML exceeds the size limit.")
    _reject_document_type(path)
    return _RepositoryReader(path).read()


class _RepositoryReader:
    """Stream the export and keep only the objects the audit needs."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._stack: list[_Node] = []
        self._tables: list[ModelTable] = []
        self._areas: list[SubjectArea] = []
        self._relationships: list[ModelRelationship] = []
        self._model_props: dict[str, str] = {}
        self._saw_repository = False

    def read(self) -> LogicalDataModel:
        elements: list[str] = []
        try:
            context = etree.iterparse(
                self._path,
                events=("start", "end"),
                huge_tree=True,
                resolve_entities=False,
                no_network=True,
            )
            for event, elem in context:
                local = etree.QName(elem).localname
                if event == "start":
                    elements.append(local)
                    self._start(local, elem)
                    continue
                parent_name = elements[-2] if len(elements) > 1 else ""
                self._end(local, (elem.text or "").strip(), parent_name)
                elements.pop()
                parent = elem.getparent()
                elem.clear()
                if parent is not None:
                    while elem.getprevious() is not None:
                        del parent[0]
        except etree.XMLSyntaxError as exc:
            raise ErwinXmlError("The XML could not be read.") from exc
        if not self._saw_repository:
            raise ErwinXmlError("The file is not an Erwin repository export.")
        return LogicalDataModel(
            name=self._model_props.get("Name", ""),
            origin_id=self._model_props.get("Long_Id", ""),
            target_server=self._model_props.get("Target_Server", ""),
            dbms_major_version=self._model_props.get("DBMS_Major_Version", ""),
            dbms_minor_version=self._model_props.get("DBMS_Minor_Version", ""),
            subject_areas=tuple(self._areas),
            tables=tuple(self._tables),
            relationships=tuple(self._relationships),
        )

    def _start(self, local: str, elem: etree._Element) -> None:
        if local == "erwin":
            if elem.get("Format") != "erwin_Repository":
                raise ErwinXmlError("Only the Erwin repository XML format is supported.")
            self._saw_repository = True
        if local in _OBJECTS:
            self._stack.append(_Node(local, elem.get("id") or ""))

    def _end(self, local: str, text: str, parent: str) -> None:
        owner = _PROPS_OF.get(parent)
        if owner is not None and self._stack and self._stack[-1].kind == owner:
            self._stack[-1].props[local] = text
        area = self._current("Subject_Area")
        if local == "User_Attached_Objects_Ref" and text and area is not None:
            area.member_refs.append(text)
        if local not in _OBJECTS or not self._stack or self._stack[-1].kind != local:
            return
        self._finish(self._stack.pop())

    def _finish(self, node: _Node) -> None:
        if node.kind == "Model":
            self._model_props = node.props
        elif node.kind == "Subject_Area":
            self._areas.append(_subject_area(node))
        elif node.kind == "Entity":
            self._tables.append(_table(node))
        elif node.kind == "Relationship":
            self._relationships.append(_relationship(node))
        elif node.kind == "Attribute":
            entity = self._current("Entity")
            if entity is not None:
                entity.attributes.append(node)
        elif node.kind == "Key_Group":
            entity = self._current("Entity")
            if entity is not None:
                entity.keys.append(node)
        elif node.kind == "Key_Group_Member":
            key_group = self._current("Key_Group")
            if key_group is not None:
                key_group.members.append(node)

    def _current(self, kind: str) -> _Node | None:
        for node in reversed(self._stack):
            if node.kind == kind:
                return node
        return None


def _reject_document_type(path: Path) -> None:
    try:
        handle = path.open("rb")
    except OSError as exc:
        raise ErwinXmlError(f"File not found: {path.name}") from exc
    with handle:
        while chunk := handle.read(1024 * 1024):
            lowered = chunk.lower()
            if b"<!doctype" in lowered or b"<!entity" in lowered:
                raise ErwinXmlError("DTD and external entities are not accepted.")


def _origin(node: _Node) -> str:
    return node.props.get("Long_Id") or node.origin_id


def _nullable(value: str) -> bool | None:
    if value == "0":
        return True
    if value == "1":
        return False
    return None


def _subject_area(node: _Node) -> SubjectArea:
    populated = node.props.get("Auto_Populate_With_All_Objects", "").casefold() == "true"
    return SubjectArea(
        origin_id=_origin(node),
        name=node.props.get("Name", ""),
        definition=node.props.get("Definition", ""),
        member_ids=tuple(node.member_refs),
        includes_all_entities=populated,
    )


def _table(node: _Node) -> ModelTable:
    return ModelTable(
        origin_id=_origin(node),
        logical_name=node.props.get("Name", ""),
        physical_name=node.props.get("Physical_Name", ""),
        definition=node.props.get("Definition", ""),
        columns=tuple(_column(item) for item in node.attributes),
        key_groups=tuple(_key_group(item) for item in node.keys),
    )


def _column(node: _Node) -> ModelColumn:
    return ModelColumn(
        origin_id=_origin(node),
        logical_name=node.props.get("Name", ""),
        physical_name=node.props.get("Physical_Name", ""),
        logical_data_type=node.props.get("Logical_Data_Type", ""),
        physical_data_type=node.props.get("Physical_Data_Type", ""),
        nullable=_nullable(node.props.get("Null_Option_Type", "")),
        definition=node.props.get("Definition", ""),
    )


def _key_group(node: _Node) -> KeyGroup:
    return KeyGroup(
        origin_id=_origin(node),
        name=node.props.get("Name", ""),
        physical_name=node.props.get("Physical_Name", ""),
        key_group_type=node.props.get("Key_Group_Type", ""),
        members=tuple(_member(item) for item in node.members),
    )


def _member(node: _Node) -> KeyMember:
    return KeyMember(
        origin_id=_origin(node),
        attribute_id=node.props.get("Attribute_Ref", ""),
        name=node.props.get("Name", ""),
        physical_name=node.props.get("Physical_Name", ""),
    )


def _relationship(node: _Node) -> ModelRelationship:
    return ModelRelationship(
        origin_id=_origin(node),
        name=node.props.get("Name", ""),
        parent_entity_id=node.props.get("Parent_Entity_Ref", ""),
        child_entity_id=node.props.get("Child_Entity_Ref", ""),
        key_group_id=node.props.get("Key_Group_Ref", ""),
    )
