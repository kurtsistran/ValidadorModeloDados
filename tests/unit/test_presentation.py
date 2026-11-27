"""Offscreen tests for the desktop widgets."""

import os
from collections.abc import Iterator

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from data_model_auditor.bootstrap.desktop_composition import (  # noqa: E402
    build_audit_workflow,
    default_rules_path,
)
from data_model_auditor.presentation.findings_model import (  # noqa: E402
    FindingsFilter,
    FindingsTableModel,
)
from data_model_auditor.presentation.main_window import MainWindow  # noqa: E402
from data_model_auditor.presentation.scope_panel import ScopePanel  # noqa: E402
from fixtures.synthetic_model import customer_order_model  # noqa: E402


@pytest.fixture(scope="module")
def application() -> Iterator[QApplication]:
    existing = QApplication.instance()
    app = existing if isinstance(existing, QApplication) else QApplication([])
    yield app


def _row(severity: str, category: str, table: str, field: str) -> tuple[str, ...]:
    location = ("Area", table, field, field)
    return (severity, category, "X-1", "Rule", *location, "msg", "", "", "", "", "1")


def test_scope_panel_does_not_choose_an_area(application: QApplication) -> None:
    panel = ScopePanel()
    panel.set_model(customer_order_model())
    assert panel.chosen_area() == ""
    assert panel.area.count() == 3


def test_scope_panel_without_marks_selects_everything(application: QApplication) -> None:
    panel = ScopePanel()
    panel.set_model(customer_order_model())
    panel.area.setCurrentIndex(panel.area.findData("All"))
    selection = panel.selection()
    assert selection.table_ids == ()
    assert selection.column_ids == ()


def test_scope_panel_partial_table_lists_its_checked_columns(application: QApplication) -> None:
    panel = ScopePanel()
    panel.set_model(customer_order_model())
    panel.area.setCurrentIndex(panel.area.findData("All"))
    tree = panel._tree
    customer = tree.topLevelItem(0)
    order = tree.topLevelItem(1)
    assert customer is not None and order is not None
    assert customer.text(0) == "CUSTOMER"
    customer.child(0).setCheckState(0, Qt.CheckState.Checked)
    order.setCheckState(0, Qt.CheckState.Checked)

    selection = panel.selection()

    assert selection.table_ids == ("customer", "order")
    assert set(selection.column_ids) == {"c1", "o1", "o2"}


def test_findings_filter_by_severity_category_and_text(application: QApplication) -> None:
    model = FindingsTableModel()
    model.set_rows(
        (
            _row("Alta", "Nomenclatura", "CUSTOMER", "CD_A"),
            _row("Média", "Índice", "ORDER", "CD_B"),
        )
    )
    proxy = FindingsFilter()
    proxy.setSourceModel(model)
    proxy.set_filters("Alta", "", "")
    assert proxy.rowCount() == 1
    proxy.set_filters("", "Índice", "")
    assert proxy.rowCount() == 1
    proxy.set_filters("", "", "cd_a")
    assert proxy.rowCount() == 1
    proxy.set_filters("", "", "")
    assert proxy.rowCount() == 2


def test_main_window_opens_without_database_or_server(application: QApplication) -> None:
    window = MainWindow(build_audit_workflow(), default_rules_path())
    window.show()
    application.processEvents()
    assert window.windowTitle() == "Data Model Auditor"
    assert not window._run_button.isEnabled()
    window._runner.wait()
    window.close()
