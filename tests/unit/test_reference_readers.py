"""Tests for the reference-document readers."""

from pathlib import Path

import pytest
import xlwt
from docx import Document
from openpyxl import Workbook

from data_model_auditor.domain.reference_catalog import NameClassColumns, ThesaurusColumns
from data_model_auditor.infrastructure.readers.sm077 import (
    SpecificationLayoutError,
    read_entity_specification,
)
from data_model_auditor.infrastructure.readers.tabular import (
    SpreadsheetLayoutError,
    read_thesaurus,
)


def test_xls_reader_uses_the_supplied_template_headers(tmp_path: Path) -> None:
    """The term and name-class sheets are discovered by their headers."""
    path = tmp_path / "thesaurus.xls"
    workbook = xlwt.Workbook()
    terms = workbook.add_sheet("thesaurus")
    for column, header in enumerate(("Termo", "Mnemônico", "Termo Preterido", "Pret. Mnemônico")):
        terms.write(0, column, header)
    terms.write(1, 0, "CLIENTE\xa0")
    terms.write(1, 1, "CLI \xa0")
    terms.write(2, 0, "ABATIDO")
    terms.write(2, 2, "DESCONTADO")
    terms.write(2, 3, "DESCD")
    classes = workbook.add_sheet("numenclatura")
    for column, header in enumerate(("Código", "Nome", "Nome Abrev", "Nome Codif", "Descrição")):
        classes.write(0, column, header)
    classes.write(1, 0, 1)
    classes.write(1, 1, "CÓDIGO")
    classes.write(1, 2, "CD")
    classes.write(1, 3, "C")
    classes.write(1, 4, "Identificador")
    workbook.save(path)

    catalog = read_thesaurus(path)

    assert catalog.entries[0].term == "CLIENTE"
    assert catalog.entries[0].mnemonic == "CLI"
    assert catalog.entries[1].deprecated_mnemonic == "DESCD"
    assert catalog.name_classes[0].abbreviation == "CD"
    assert catalog.name_classes[0].code == "1"


def test_xlsx_accepts_an_explicit_column_map(tmp_path: Path) -> None:
    """A spreadsheet with other headers is read only after the columns are mapped."""
    path = tmp_path / "terms.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = "terms"
    sheet.append(["word", "short", "old", "old_short"])
    sheet.append(["CONTA", "CTA", "", ""])
    classes = workbook.create_sheet("classes")
    classes.append(["id", "title", "prefix", "letter", "meaning"])
    classes.append(["2", "DATA", "DT", "D", "Tempo"])
    workbook.save(path)

    with pytest.raises(SpreadsheetLayoutError):
        read_thesaurus(path)

    catalog = read_thesaurus(
        path,
        term_columns=ThesaurusColumns(
            term="word",
            mnemonic="short",
            deprecated_term="old",
            deprecated_mnemonic="old_short",
        ),
        class_columns=NameClassColumns(
            code="id",
            name="title",
            abbreviation="prefix",
            coded_name="letter",
            description="meaning",
        ),
    )

    assert catalog.entries[0].mnemonic == "CTA"
    assert catalog.name_classes[0].abbreviation == "DT"


def test_csv_uses_the_same_column_contract(tmp_path: Path) -> None:
    """CSV rows use the same term and name-class columns as the workbook."""
    path = tmp_path / "terms.csv"
    header = (
        "Termo,Mnemônico,Termo Preterido,Pret. Mnemônico,"
        "Código,Nome,Nome Abrev,Nome Codif,Descrição"
    )
    path.write_text(
        f"{header}\nCONTA,CTA,,,,,,,\n,,,,2,DATA,DT,D,Tempo\n",
        encoding="utf-8",
    )

    catalog = read_thesaurus(path)

    assert catalog.entries[0].mnemonic == "CTA"
    assert catalog.name_classes[0].abbreviation == "DT"


def test_spreadsheet_rejects_missing_empty_and_unknown_files(tmp_path: Path) -> None:
    """A missing, empty, or unsupported spreadsheet becomes a layout error."""
    with pytest.raises(SpreadsheetLayoutError):
        read_thesaurus(tmp_path / "missing.xls")
    for name in ("empty.xls", "empty.xlsx", "empty.csv"):
        (tmp_path / name).write_bytes(b"")
        with pytest.raises(SpreadsheetLayoutError):
            read_thesaurus(tmp_path / name)
    (tmp_path / "notes.txt").write_text("not a spreadsheet", encoding="utf-8")
    with pytest.raises(SpreadsheetLayoutError):
        read_thesaurus(tmp_path / "notes.txt")

def test_sm077_reads_the_column_table(tmp_path: Path) -> None:
    """The entity specification preserves physical names and nullability."""
    path = tmp_path / "SM077.docx"
    document = Document()
    labels = document.add_table(rows=2, cols=2)
    labels.rows[0].cells[0].text = "NOME DA ENTIDADE:"
    labels.rows[0].cells[1].text = "PARCELAS / DBSVGB.PARCELAS"
    labels.rows[1].cells[0].text = "DESCRIÇÃO DA ENTIDADE:"
    labels.rows[1].cells[1].text = "Armazena as parcelas."
    columns = document.add_table(rows=2, cols=5)
    headers = ("OPER (*)", "DOMÍNIO LÓGICO", "DOMÍNIO FÍSICO", "DATATYPE", "OBSERVAÇÕES")
    for index, header in enumerate(headers):
        columns.rows[0].cells[index].text = header
    values = ("A", "PAR_VL_MENSAL", "PAR_VL_MENSAL", "DECIMAL(11, 2) NOT NULL", "Valor da parcela")
    for index, value in enumerate(values):
        columns.rows[1].cells[index].text = value
    document.save(path)

    specification = read_entity_specification(path)

    assert specification.fields[0].value == "PARCELAS / DBSVGB.PARCELAS"
    column = specification.columns[0]
    assert column.physical_name == "PAR_VL_MENSAL"
    assert column.nullable is False
    assert column.observations == "Valor da parcela"


def test_sm077_rejects_missing_empty_and_header_only_documents(tmp_path: Path) -> None:
    """A specification without the column table is not accepted."""
    with pytest.raises(SpecificationLayoutError):
        read_entity_specification(tmp_path / "missing.docx")
    empty = tmp_path / "empty.docx"
    empty.write_bytes(b"")
    with pytest.raises(SpecificationLayoutError):
        read_entity_specification(empty)
    header_only = tmp_path / "labels.docx"
    document = Document()
    labels = document.add_table(rows=1, cols=2)
    labels.rows[0].cells[0].text = "NOME DA ENTIDADE:"
    labels.rows[0].cells[1].text = "PARCELAS"
    document.save(header_only)
    with pytest.raises(SpecificationLayoutError):
        read_entity_specification(header_only)

