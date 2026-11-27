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
