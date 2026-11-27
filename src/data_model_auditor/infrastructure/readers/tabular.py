"""Read term and name-class spreadsheets without assuming a fixed file name."""

from pathlib import Path
from zipfile import BadZipFile

import pandas as pd

from data_model_auditor.domain.reference_catalog import (
    NameClass,
    NameClassColumns,
    ThesaurusCatalog,
    ThesaurusColumns,
    ThesaurusEntry,
)

_MAX_BYTES = 20 * 1024 * 1024


class SpreadsheetLayoutError(Exception):
    """Raised when a spreadsheet does not contain the requested columns."""


def read_thesaurus(
    path: Path,
    term_columns: ThesaurusColumns | None = None,
    class_columns: NameClassColumns | None = None,
) -> ThesaurusCatalog:
    """Read the term sheet and the name-class sheet from one workbook or CSV."""
    sheets = _read_sheets(path)
    terms = term_columns or ThesaurusColumns()
    classes = class_columns or NameClassColumns()
    term_sheet = _sheet_with_columns(
        sheets,
        (terms.term, terms.mnemonic, terms.deprecated_term, terms.deprecated_mnemonic),
    )
    class_sheet = _sheet_with_columns(
        sheets,
        (classes.code, classes.name, classes.abbreviation, classes.coded_name, classes.description),
    )
    return ThesaurusCatalog(
        entries=tuple(_entries(term_sheet, terms)),
        name_classes=tuple(_classes(class_sheet, classes)),
    )


def _read_sheets(path: Path) -> dict[str, pd.DataFrame]:
    if not path.is_file():
        raise SpreadsheetLayoutError(f"File not found: {path.name}")
    if path.stat().st_size > _MAX_BYTES:
        raise SpreadsheetLayoutError("The spreadsheet exceeds the size limit.")
    suffix = path.suffix.lower()
    try:
        if suffix == ".csv":
            frames = {"csv": pd.read_csv(path, dtype=str, keep_default_na=False)}
        elif suffix == ".xls":
            frames = pd.read_excel(path, sheet_name=None, dtype=str, engine="xlrd")
        elif suffix == ".xlsx":
            frames = pd.read_excel(path, sheet_name=None, dtype=str, engine="openpyxl")
        else:
            raise SpreadsheetLayoutError("Use a CSV, XLS, or XLSX file.")
    except SpreadsheetLayoutError:
        raise
    except Exception as exc:
        if not _is_read_failure(exc):
            raise
        raise SpreadsheetLayoutError("The spreadsheet could not be read.") from exc
    return {str(name): frame.fillna("") for name, frame in frames.items()}


def _is_read_failure(exc: Exception) -> bool:
    if isinstance(
        exc,
        (
            BadZipFile,
            OSError,
            TypeError,
            UnicodeError,
            ValueError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ),
    ):
        return True
    return type(exc).__module__.startswith("xlrd")


def _sheet_with_columns(
    sheets: dict[str, pd.DataFrame],
    required: tuple[str, ...],
) -> pd.DataFrame:
    needed = {_normalize_header(name) for name in required}
    found: list[str] = []
    for frame in sheets.values():
        headers = [_normalize_header(str(column)) for column in frame.columns]
        found.extend(headers)
        if needed.issubset(headers):
            return frame
    readable = ", ".join(sorted(set(found))) or "(none)"
    raise SpreadsheetLayoutError(f"Required columns were not found. Found: {readable}")


def _entries(frame: pd.DataFrame, columns: ThesaurusColumns) -> list[ThesaurusEntry]:
    rows: list[ThesaurusEntry] = []
    for record in _records(frame):
        term = _cell(record, columns.term)
        if not term:
            continue
        rows.append(
            ThesaurusEntry(
                term=term,
                mnemonic=_cell(record, columns.mnemonic),
                deprecated_term=_cell(record, columns.deprecated_term),
                deprecated_mnemonic=_cell(record, columns.deprecated_mnemonic),
            )
        )
    return rows


def _classes(frame: pd.DataFrame, columns: NameClassColumns) -> list[NameClass]:
    rows: list[NameClass] = []
    for record in _records(frame):
        name = _cell(record, columns.name)
        abbreviation = _cell(record, columns.abbreviation)
        if not name and not abbreviation:
            continue
        rows.append(
            NameClass(
                code=_cell(record, columns.code),
                name=name,
                abbreviation=abbreviation,
                coded_name=_cell(record, columns.coded_name),
                description=_cell(record, columns.description),
            )
        )
    return rows


def _records(frame: pd.DataFrame) -> list[dict[str, str]]:
    normalized = {_normalize_header(str(column)): column for column in frame.columns}
    records: list[dict[str, str]] = []
    for raw in frame.to_dict(orient="records"):
        records.append(
            {
                header: _clean(raw[original])
                for header, original in normalized.items()
            }
        )
    return records


def _cell(record: dict[str, str], header: str) -> str:
    return record.get(_normalize_header(header), "")


def _normalize_header(value: str) -> str:
    return _clean(value).casefold()


def _clean(value: object) -> str:
    text = str(value).replace("\xa0", " ").replace("\u00a0", " ")
    text = " ".join(text.split())
    if len(text) > 2 and text.endswith(".0") and text[:-2].isdigit():
        return text[:-2]
    return text
