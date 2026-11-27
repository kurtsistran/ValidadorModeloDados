"""Table model and filters for the findings view."""

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    QSortFilterProxyModel,
    Qt,
)

from data_model_auditor.application.report_content import FINDING_HEADERS

_ALL = ""
_SEVERITY, _CATEGORY = 0, 1
_TABLE, _PHYSICAL, _LOGICAL, _MESSAGE = 5, 6, 7, 8
_VISIBLE_COLUMNS = (0, 1, 2, 5, 6, 7, 8)
_Index = QModelIndex | QPersistentModelIndex


class FindingsTableModel(QAbstractTableModel):
    """Expose finding rows built by the report content."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: tuple[tuple[str, ...], ...] = ()

    def set_rows(self, rows: tuple[tuple[str, ...], ...]) -> None:
        """Replace every row."""
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def row_values(self, row: int) -> tuple[str, ...]:
        """All cells of one source row, including hidden ones."""
        return self._rows[row]

    # Qt calls these overrides by name; the default index is the Qt convention.
    def rowCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: _Index = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(_VISIBLE_COLUMNS)

    def data(self, index: _Index, role: int = Qt.ItemDataRole.DisplayRole) -> object:
        if role != Qt.ItemDataRole.DisplayRole or not index.isValid():
            return None
        return self._rows[index.row()][_VISIBLE_COLUMNS[index.column()]]

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object:
        if role != Qt.ItemDataRole.DisplayRole or orientation != Qt.Orientation.Horizontal:
            return None
        return FINDING_HEADERS[_VISIBLE_COLUMNS[section]]


class FindingsFilter(QSortFilterProxyModel):
    """Filter by severity, category, and free text over table and field names."""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._severity = _ALL
        self._category = _ALL
        self._text = ""

    def set_filters(self, severity: str, category: str, text: str) -> None:
        """Apply new filter values. An empty value accepts everything."""
        self.beginFilterChange()
        self._severity = severity
        self._category = category
        self._text = text.strip().casefold()
        self.endFilterChange(QSortFilterProxyModel.Direction.Rows)

    def filterAcceptsRow(self, source_row: int, source_parent: _Index) -> bool:
        model = self.sourceModel()
        if not isinstance(model, FindingsTableModel):
            return True
        row = model.row_values(source_row)
        if self._severity and row[_SEVERITY] != self._severity:
            return False
        if self._category and row[_CATEGORY] != self._category:
            return False
        if not self._text:
            return True
        searchable = " ".join(row[index] for index in (_TABLE, _PHYSICAL, _LOGICAL, _MESSAGE))
        return self._text in searchable.casefold()
