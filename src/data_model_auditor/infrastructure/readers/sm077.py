"""Read an SM077 Word specification without executing document content."""

import re
from pathlib import Path

from docx import Document
from docx.document import Document as WordDocument
from docx.opc.exceptions import PackageNotFoundError
from docx.table import Table

from data_model_auditor.domain.reference_catalog import (
    DocumentedColumn,
    EntitySpecification,
    LabeledValue,
)

_MAX_BYTES = 20 * 1024 * 1024
_NULLABILITY = re.compile(r"\bNOT NULL\b|\bNULL\b", re.IGNORECASE)


class SpecificationLayoutError(Exception):
    """Raised when the Word file does not contain the SM077 field table."""


def read_entity_specification(path: Path) -> EntitySpecification:
    """Read labels and the column-maintenance table from an SM077 document."""
    if not path.is_file():
        raise SpecificationLayoutError(f"File not found: {path.name}")
    if path.stat().st_size > _MAX_BYTES:
        raise SpecificationLayoutError("The document exceeds the size limit.")
    if path.suffix.lower() != ".docx":
        raise SpecificationLayoutError("The specification must be a DOCX file.")
    try:
        document = Document(str(path))
    except (OSError, PackageNotFoundError, ValueError) as exc:
        raise SpecificationLayoutError("The specification could not be read.") from exc
    fields = _labels(document)
    columns = _columns(document)
    if not columns:
        raise SpecificationLayoutError("The column table was not found.")
    return EntitySpecification(fields=tuple(fields), columns=tuple(columns))


def _labels(document: WordDocument) -> list[LabeledValue]:
    found: list[LabeledValue] = []
    for table in document.tables:
        for row in table.rows:
            cells = [_clean(cell.text) for cell in row.cells]
            for index, text in enumerate(cells[:-1]):
                if text.endswith(":") and cells[index + 1] and cells[index + 1] != text:
                    found.append(LabeledValue(label=text[:-1].strip(), value=cells[index + 1]))
    return found


def _columns(document: WordDocument) -> list[DocumentedColumn]:
    for table in document.tables:
        parsed = _column_table(table)
        if parsed:
            return parsed
    return []


def _column_table(table: Table) -> list[DocumentedColumn]:
    rows = [[_clean(cell.text) for cell in row.cells] for row in table.rows]
    header_index = next(
        (index for index, row in enumerate(rows) if "domínio físico" in _headers(row)),
        None,
    )
    if header_index is None:
        return []
    positions = {name: position for position, name in enumerate(_headers(rows[header_index]))}
    required = ("oper (*)", "domínio lógico", "domínio físico", "datatype", "observações")
    if not set(required).issubset(positions):
        return []
    columns: list[DocumentedColumn] = []
    for row in rows[header_index + 1 :]:
        physical = _at(row, positions["domínio físico"])
        logical = _at(row, positions["domínio lógico"])
        if not physical and not logical:
            continue
        data_type = _at(row, positions["datatype"])
        columns.append(
            DocumentedColumn(
                operation=_at(row, positions["oper (*)"]),
                logical_name=logical,
                physical_name=physical,
                data_type=data_type,
                nullable=_nullable(data_type),
                observations=_at(row, positions["observações"]),
            )
        )
    return columns


def _headers(row: list[str]) -> list[str]:
    return [cell.casefold() for cell in row]


def _at(row: list[str], position: int) -> str:
    if position >= len(row):
        return ""
    return row[position]


def _nullable(data_type: str) -> bool | None:
    match = _NULLABILITY.search(data_type)
    if match is None:
        return None
    return match.group(0).upper() != "NOT NULL"


def _clean(value: str) -> str:
    return " ".join(value.replace("\xa0", " ").split())
