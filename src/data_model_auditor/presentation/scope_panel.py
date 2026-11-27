"""Subject-area choice and optional table and column selection."""

from dataclasses import dataclass

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from data_model_auditor.domain.audit_scope import select_audit_scope
from data_model_auditor.domain.data_model import LogicalDataModel

_ID_ROLE = Qt.ItemDataRole.UserRole
_PLACEHOLDER = "Selecione a Subject Area"
_CHECKED = Qt.CheckState.Checked
_UNCHECKED = Qt.CheckState.Unchecked


@dataclass(frozen=True)
class ScopeSelection:
    """Identifiers chosen in the tree. Empty tuples mean everything in the area."""

    table_ids: tuple[str, ...]
    column_ids: tuple[str, ...]


class ScopePanel(QWidget):
    """Mandatory subject area plus an optional tree of tables and columns."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model: LogicalDataModel | None = None
        self.area = QComboBox()
        self.area.setMinimumWidth(320)
        self._filter = QLineEdit()
        self._filter.setPlaceholderText("Filtrar tabelas pelo nome")
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(["Tabela / campo", "Nome lógico", "Tipo"])
        self._tree.setColumnWidth(0, 320)
        self._tree.setColumnWidth(1, 260)
        self._hint = QLabel(
            "Sem marcação, todas as tabelas e campos da Subject Area são auditados."
        )
        self._hint.setWordWrap(True)
        form = QFormLayout()
        form.addRow("Subject Area (obrigatória):", self.area)
        form.addRow("Filtro:", self._filter)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(self._hint)
        layout.addWidget(self._tree)
        self.area.currentIndexChanged.connect(self._fill_tree)
        self._filter.textChanged.connect(self._apply_filter)

    def set_model(self, model: LogicalDataModel) -> None:
        """Show the areas of a newly loaded model. No area is chosen for the user."""
        self._model = model
        self.area.blockSignals(True)
        self.area.clear()
        self.area.addItem(_PLACEHOLDER, "")
        for area in sorted(model.subject_areas, key=lambda item: item.name.casefold()):
            self.area.addItem(area.name, area.name)
        self.area.blockSignals(False)
        self._tree.clear()
        if not model.subject_areas:
            self._hint.setText(
                "O modelo não tem Subject Area identificável. A auditoria não pode começar."
            )

    def chosen_area(self) -> str:
        """The selected area name, or an empty text."""
        value = self.area.currentData()
        return value if isinstance(value, str) else ""

    def selection(self) -> ScopeSelection:
        """Translate the check marks into scope identifiers."""
        tables: list[str] = []
        partial_columns: list[str] = []
        full_columns: list[str] = []
        any_partial = False
        for index in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(index)
            if item is None or item.checkState(0) == _UNCHECKED:
                continue
            tables.append(str(item.data(0, _ID_ROLE)))
            children = [item.child(position) for position in range(item.childCount())]
            ids = [str(child.data(0, _ID_ROLE)) for child in children if child is not None]
            checked = [
                str(child.data(0, _ID_ROLE))
                for child in children
                if child is not None and child.checkState(0) == _CHECKED
            ]
            if item.checkState(0) == Qt.CheckState.PartiallyChecked:
                any_partial = True
                partial_columns.extend(checked)
            else:
                full_columns.extend(ids)
        columns = (*full_columns, *partial_columns) if any_partial else ()
        return ScopeSelection(tuple(tables), tuple(columns))

    def _fill_tree(self) -> None:
        self._tree.clear()
        name = self.chosen_area()
        if self._model is None or not name:
            return
        scope = select_audit_scope(self._model, name)
        items: list[QTreeWidgetItem] = []
        for table in sorted(scope.tables, key=lambda item: item.physical_name):
            parent = QTreeWidgetItem([table.physical_name, table.logical_name, ""])
            parent.setData(0, _ID_ROLE, table.origin_id)
            parent.setFlags(parent.flags() | Qt.ItemFlag.ItemIsAutoTristate)
            parent.setCheckState(0, _UNCHECKED)
            for column in table.columns:
                child = QTreeWidgetItem(
                    [column.physical_name, column.logical_name, column.physical_data_type]
                )
                child.setData(0, _ID_ROLE, column.origin_id)
                child.setCheckState(0, _UNCHECKED)
                parent.addChild(child)
            items.append(parent)
        self._tree.addTopLevelItems(items)
        self._hint.setText(
            f"{len(items)} tabelas na Subject Area. Sem marcação, todas são auditadas."
        )
        self._apply_filter(self._filter.text())

    def _apply_filter(self, text: str) -> None:
        needle = text.strip().casefold()
        for index in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(index)
            if item is not None:
                item.setHidden(bool(needle) and needle not in item.text(0).casefold())
