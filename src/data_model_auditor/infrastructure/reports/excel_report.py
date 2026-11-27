"""Write the audit report as an XLSX workbook."""

from pathlib import Path

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet._write_only import WriteOnlyWorksheet

from data_model_auditor.application.report_content import ReportContent, ReportSheet
from data_model_auditor.infrastructure.reports.errors import ReportWriteError

_HEADER_FONT = Font(bold=True, color="FFFFFF")
_HEADER_FILL = PatternFill("solid", fgColor="1F4E79")
_MAX_WIDTH = 60
_MIN_WIDTH = 10
_WIDTH_SAMPLE = 200


def write_excel_report(content: ReportContent, path: Path) -> None:
    """Write the five report sheets to ``path``."""
    if path.suffix.lower() != ".xlsx":
        raise ReportWriteError("The Excel report must use the .xlsx extension.")
    workbook = Workbook(write_only=True)
    for sheet in content.sheets():
        _write_sheet(workbook.create_sheet(sheet.title), sheet)
    try:
        workbook.save(path)
    except OSError as exc:
        raise ReportWriteError(f"The report could not be saved: {path.name}") from exc


def _write_sheet(worksheet: WriteOnlyWorksheet, sheet: ReportSheet) -> None:
    # Write-only sheets keep column widths and filters at runtime; types-openpyxl omits them.
    for index, width in enumerate(_widths(sheet), start=1):
        dimensions = worksheet.column_dimensions  # type: ignore[attr-defined]
        dimensions[get_column_letter(index)].width = width
    worksheet.freeze_panes = "A2"
    headers = []
    for title in sheet.headers:
        cell = WriteOnlyCell(worksheet, value=title)
        cell.font = _HEADER_FONT
        cell.fill = _HEADER_FILL
        cell.alignment = Alignment(vertical="center")
        headers.append(cell)
    worksheet.append(headers)
    for row in sheet.rows:
        worksheet.append(list(row))
    if sheet.rows:
        last = get_column_letter(len(sheet.headers))
        worksheet.auto_filter.ref = (  # type: ignore[attr-defined]
            f"A1:{last}{len(sheet.rows) + 1}"
        )


def _widths(sheet: ReportSheet) -> list[int]:
    widths = [len(title) for title in sheet.headers]
    for row in sheet.rows[:_WIDTH_SAMPLE]:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))
    return [min(max(width + 2, _MIN_WIDTH), _MAX_WIDTH) for width in widths]
