"""Findings table with filters, detail, and export buttons."""

from collections.abc import Iterable

from PySide6.QtCore import QModelIndex, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from data_model_auditor.application.report_content import (
    CATEGORY_LABELS,
    FINDING_HEADERS,
    SEVERITY_LABELS,
)
from data_model_auditor.presentation.findings_model import FindingsFilter, FindingsTableModel

_ALL = "Todas"


class ResultsPanel(QWidget):
    """Show the findings of the last run."""

    export_excel_requested = Signal()
    export_pdf_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model = FindingsTableModel(self)
        self._proxy = FindingsFilter(self)
        self._proxy.setSourceModel(self._model)
        self._summary = QLabel("Nenhuma auditoria executada.")
        self._severity = _combo(SEVERITY_LABELS.values())
        self._category = _combo(CATEGORY_LABELS.values())
        self._text = QLineEdit()
        self._text.setPlaceholderText("Tabela, campo ou texto da inconsistência")
        self._view = QTableView()
        self._view.setModel(self._proxy)
        self._view.setSortingEnabled(True)
        self._view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._view.horizontalHeader().setStretchLastSection(True)
        self._detail = QPlainTextEdit()
        self._detail.setReadOnly(True)
        self._detail.setPlaceholderText("Selecione uma inconsistência para ver os detalhes.")
        self.excel_button = QPushButton("Exportar Excel")
        self.pdf_button = QPushButton("Exportar PDF")
        self.set_export_enabled(False)
        self._layout()
        self._severity.currentIndexChanged.connect(self._refilter)
        self._category.currentIndexChanged.connect(self._refilter)
        self._text.textChanged.connect(self._refilter)
        self._view.selectionModel().currentRowChanged.connect(self._show_detail)
        self.excel_button.clicked.connect(self.export_excel_requested)
        self.pdf_button.clicked.connect(self.export_pdf_requested)

    def _layout(self) -> None:
        filters = QHBoxLayout()
        filters.addWidget(QLabel("Severidade:"))
        filters.addWidget(self._severity)
        filters.addWidget(QLabel("Categoria:"))
        filters.addWidget(self._category)
        filters.addWidget(QLabel("Busca:"))
        filters.addWidget(self._text, 1)
        exports = QHBoxLayout()
        exports.addWidget(self._summary, 1)
        exports.addWidget(self.excel_button)
        exports.addWidget(self.pdf_button)
        splitter = QSplitter()
        splitter.addWidget(self._view)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        layout.addLayout(exports)
        layout.addLayout(filters)
        layout.addWidget(splitter, 1)

    def show_rows(self, rows: tuple[tuple[str, ...], ...], summary: str) -> None:
        """Replace the findings and the summary line."""
        self._model.set_rows(rows)
        self._summary.setText(summary)
        self._detail.clear()
        self._view.resizeColumnsToContents()
        self.set_export_enabled(True)

    def set_export_enabled(self, enabled: bool) -> None:
        """Exports need a completed run."""
        self.excel_button.setEnabled(enabled)
        self.pdf_button.setEnabled(enabled)

    def _refilter(self) -> None:
        self._proxy.set_filters(
            _value(self._severity),
            _value(self._category),
            self._text.text(),
        )

    def _show_detail(self, current: QModelIndex, _previous: QModelIndex) -> None:
        if not current.isValid():
            self._detail.clear()
            return
        source = self._proxy.mapToSource(current)
        values = self._model.row_values(source.row())
        lines = [f"{title}: {value}" for title, value in zip(FINDING_HEADERS, values, strict=True)]
        self._detail.setPlainText("\n\n".join(line for line in lines if not line.endswith(": ")))


def _combo(values: Iterable[str]) -> QComboBox:
    combo = QComboBox()
    combo.addItem(_ALL)
    for value in values:
        combo.addItem(value)
    return combo


def _value(combo: QComboBox) -> str:
    text = combo.currentText()
    return "" if text == _ALL else text
