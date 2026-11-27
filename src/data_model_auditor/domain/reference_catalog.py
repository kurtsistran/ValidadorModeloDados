"""Internal representation of reference documents.

The field names follow the templates supplied for this project. A spreadsheet
with different headers is accepted through an explicit column map.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ThesaurusColumns:
    """Headers that identify the term sheet."""

    term: str = "Termo"
    mnemonic: str = "Mnemônico"
    deprecated_term: str = "Termo Preterido"
    deprecated_mnemonic: str = "Pret. Mnemônico"


@dataclass(frozen=True)
class NameClassColumns:
    """Headers that identify the name-class sheet."""

    code: str = "Código"
    name: str = "Nome"
    abbreviation: str = "Nome Abrev"
    coded_name: str = "Nome Codif"
    description: str = "Descrição"


@dataclass(frozen=True)
class ThesaurusEntry:
    """One row from the term sheet, including a deprecated form when present."""

    term: str
    mnemonic: str
    deprecated_term: str
    deprecated_mnemonic: str


@dataclass(frozen=True)
class NameClass:
    """One allowed name class, such as the abbreviation used as a prefix."""

    code: str
    name: str
    abbreviation: str
    coded_name: str
    description: str


@dataclass(frozen=True)
class ThesaurusCatalog:
    """Terms and name classes read from the reference spreadsheet."""

    entries: tuple[ThesaurusEntry, ...]
    name_classes: tuple[NameClass, ...]


@dataclass(frozen=True)
class DocumentedColumn:
    """A column described in an SM077 entity specification."""

    operation: str
    logical_name: str
    physical_name: str
    data_type: str
    nullable: bool | None
    observations: str


@dataclass(frozen=True)
class LabeledValue:
    """A label and the adjacent value found in the specification."""

    label: str
    value: str


@dataclass(frozen=True)
class EntitySpecification:
    """Entity definition read from an SM077 Word document."""

    fields: tuple[LabeledValue, ...]
    columns: tuple[DocumentedColumn, ...]


@dataclass(frozen=True)
class PdfPageText:
    """Text extracted from one PDF page. It is not an approved rule."""

    number: int
    text: str


@dataclass(frozen=True)
class PdfExtraction:
    """Text of a modeling standard kept inactive until a person approves rules."""

    sha256: str
    pages: tuple[PdfPageText, ...]
    rules_active: bool = False
