"""Write the audit report as a PDF with PyMuPDF, already used to read PDFs."""

import textwrap
from pathlib import Path

import pymupdf  # type: ignore[import-untyped, unused-ignore]

from data_model_auditor.application.report_content import ReportContent
from data_model_auditor.infrastructure.reports.errors import ReportWriteError

_PAGE_WIDTH, _PAGE_HEIGHT = 595, 842
_MARGIN = 40
_TEXT = (0.1, 0.1, 0.1)
_MUTED = (0.4, 0.4, 0.4)
_ACCENT = (0.12, 0.31, 0.47)
# Helvetica averages about half the font size per character. Wrapping by this
# estimate avoids measuring every word in reports with tens of thousands of lines.
_CHAR_WIDTH_RATIO = 0.52
_LINE_SPACING = 1.35
_Color = tuple[float, float, float]


class _Canvas:
    """Sequential text layout that writes each page in one batch.

    One ``TextWriter`` per color is flushed when the page is full. Writing line
    by line with ``insert_text`` took minutes for reports with thousands of pages.
    """

    def __init__(self) -> None:
        self.document = pymupdf.open()  # type: ignore[no-untyped-call, unused-ignore]
        self._regular = pymupdf.Font("helv")  # type: ignore[no-untyped-call, unused-ignore]
        self._bold = pymupdf.Font("hebo")  # type: ignore[no-untyped-call, unused-ignore]
        self._writers: dict[_Color, object] = {}
        self._y = float(_MARGIN)

    def write(
        self,
        text: str,
        size: float = 9,
        *,
        bold: bool = False,
        color: _Color = _TEXT,
        indent: float = 0,
    ) -> None:
        """Write ``text`` wrapped to the page width."""
        usable = _PAGE_WIDTH - 2 * _MARGIN - indent
        width = max(int(usable / (size * _CHAR_WIDTH_RATIO)), 10)
        font = self._bold if bold else self._regular
        for line in textwrap.wrap(text, width=width) or [""]:
            step = size * _LINE_SPACING
            if self._y + step > _PAGE_HEIGHT - _MARGIN:
                self._flush()
            self._y += step
            writer = self._writer(color)
            writer.append(  # type: ignore[attr-defined]
                (_MARGIN + indent, self._y), line, font=font, fontsize=size
            )

    def gap(self, height: float = 6) -> None:
        """Leave vertical space."""
        self._y += height

    def finish(self) -> None:
        """Write the last page and number every footer."""
        self._flush()
        total = int(self.document.page_count)
        for index in range(total):
            page = self.document.load_page(index)  # type: ignore[no-untyped-call, unused-ignore]
            writer = pymupdf.TextWriter(page.rect)  # type: ignore[no-untyped-call, unused-ignore]
            writer.append(  # type: ignore[no-untyped-call, unused-ignore]
                (_PAGE_WIDTH - _MARGIN - 60, _PAGE_HEIGHT - _MARGIN / 2),
                f"Página {index + 1} de {total}",
                font=self._regular,
                fontsize=7,
            )
            writer.write_text(page, color=_MUTED)  # type: ignore[no-untyped-call, unused-ignore]

    def _writer(self, color: _Color) -> object:
        writer = self._writers.get(color)
        if writer is None:
            rect = pymupdf.Rect(0, 0, _PAGE_WIDTH, _PAGE_HEIGHT)  # type: ignore[no-untyped-call, unused-ignore]
            writer = pymupdf.TextWriter(rect)  # type: ignore[no-untyped-call, unused-ignore]
            self._writers[color] = writer
        return writer

    def _flush(self) -> None:
        if self._writers:
            page = self.document.new_page(  # type: ignore[no-untyped-call, unused-ignore]
                width=_PAGE_WIDTH, height=_PAGE_HEIGHT
            )
            for color, writer in self._writers.items():
                writer.write_text(page, color=color)  # type: ignore[attr-defined]
        self._writers = {}
        self._y = float(_MARGIN)


def write_pdf_report(content: ReportContent, path: Path) -> None:
    """Write the executive summary, statistics, and detailed findings."""
    if path.suffix.lower() != ".pdf":
        raise ReportWriteError("The PDF report must use the .pdf extension.")
    canvas = _Canvas()
    canvas.write("Relatório de auditoria do modelo de dados", 16, bold=True, color=_ACCENT)
    canvas.gap(8)
    canvas.write("Resumo executivo", 12, bold=True, color=_ACCENT)
    for label, value in content.summary.rows:
        canvas.write(f"{label}: {value}")
    canvas.gap(8)
    canvas.write("Configuração da execução", 12, bold=True, color=_ACCENT)
    for item, value, detail in content.configuration.rows:
        canvas.write(f"{item}: {value}" + (f" ({detail})" if detail else ""), 8)
    canvas.gap(8)
    canvas.write("Inconsistências", 12, bold=True, color=_ACCENT)
    if not content.findings.rows:
        canvas.write("Nenhuma inconsistência encontrada.")
    for row in content.findings.rows:
        _write_finding(canvas, row)
    canvas.finish()
    try:
        canvas.document.save(  # type: ignore[no-untyped-call, unused-ignore]
            str(path), garbage=1, deflate=True
        )
    except (OSError, RuntimeError, ValueError) as exc:
        raise ReportWriteError(f"The report could not be saved: {path.name}") from exc
    finally:
        canvas.document.close()  # type: ignore[no-untyped-call, unused-ignore]


def _write_finding(canvas: _Canvas, row: tuple[str, ...]) -> None:
    (
        severity,
        category,
        code,
        rule_name,
        _area,
        table,
        physical,
        _logical,
        message,
        justification,
        suggestion,
        source,
        page,
        version,
    ) = row
    place = f"{table}.{physical}" if physical else table
    canvas.gap(4)
    canvas.write(f"[{severity}] {code} · {category} · {place}", 9, bold=True)
    canvas.write(message, indent=8)
    canvas.write(f"Regra: {rule_name}", 8, indent=8, color=_MUTED)
    canvas.write(f"Justificativa: {justification}", 8, indent=8)
    canvas.write(f"Sugestão: {suggestion}", 8, indent=8)
    origin = f"Fonte: {source} · versão {version}" + (f" · página {page}" if page else "")
    canvas.write(origin, 7, indent=8, color=_MUTED)
