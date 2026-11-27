"""List the YAML rules and let the user disable them explicitly."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem, QWidget

from data_model_auditor.application.report_content import category_label, severity_label
from data_model_auditor.domain.rule_catalog import RequiredReference, RuleCatalog

_HEADERS = ("Executar", "Código", "Regra", "Categoria", "Severidade", "Referência exigida")
_REFERENCE_LABELS = {
    RequiredReference.NONE: "Nenhuma",
    RequiredReference.THESAURUS: "Thesaurus",
    RequiredReference.SM077: "SM077",
}


class RulesPanel(QTableWidget):
    """One row per rule. Unchecking a row disables the rule for this run only."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(_HEADERS), parent)
        self.setHorizontalHeaderLabels(list(_HEADERS))
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._codes: list[str] = []

    def set_catalog(self, catalog: RuleCatalog) -> None:
        """Show the rules as the YAML file defines them."""
        self.setRowCount(len(catalog.rules))
        self._codes = [rule.code for rule in catalog.rules]
        for row, rule in enumerate(catalog.rules):
            check = QTableWidgetItem()
            check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            check.setCheckState(Qt.CheckState.Checked if rule.enabled else Qt.CheckState.Unchecked)
            self.setItem(row, 0, check)
            values = (
                rule.code,
                rule.name,
                category_label(rule.category.value),
                severity_label(rule.severity),
                _REFERENCE_LABELS[rule.required_reference],
            )
            for column, value in enumerate(values, start=1):
                self.setItem(row, column, QTableWidgetItem(value))
        self.resizeColumnsToContents()

    def disabled_codes(self) -> frozenset[str]:
        """Rules the user unchecked."""
        disabled: set[str] = set()
        for row, code in enumerate(self._codes):
            item = self.item(row, 0)
            if item is not None and item.checkState() == Qt.CheckState.Unchecked:
                disabled.add(code)
        return frozenset(disabled)
