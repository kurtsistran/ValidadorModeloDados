"""Main window of the local audit. It holds no business rule."""

from collections import Counter
from pathlib import Path

from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from data_model_auditor.application.audit_service import AuditRequest, AuditResult
from data_model_auditor.application.audit_workflow import AuditSession, AuditWorkflow, LoadedModel
from data_model_auditor.application.report_content import finding_row, severity_label
from data_model_auditor.domain.rule_catalog import RuleCatalog
from data_model_auditor.domain.target_database import TargetDatabase, target_from_erwin
from data_model_auditor.presentation.file_picker import FilePicker
from data_model_auditor.presentation.results_panel import ResultsPanel
from data_model_auditor.presentation.rules_panel import RulesPanel
from data_model_auditor.presentation.scope_panel import ScopePanel
from data_model_auditor.presentation.workers import BackgroundRunner

_TARGET_LABELS = {
    TargetDatabase.SQLSERVER: "SQL Server",
    TargetDatabase.ORACLE: "Oracle",
    TargetDatabase.POSTGRESQL: "PostgreSQL",
}
_RESULT_TAB = 3


class MainWindow(QMainWindow):
    """Four steps: files, scope, rules, and results."""

    def __init__(self, workflow: AuditWorkflow, default_rules: Path) -> None:
        super().__init__()
        self.setWindowTitle("Data Model Auditor")
        self.resize(1280, 800)
        self._workflow = workflow
        self._runner = BackgroundRunner(self)
        self._loaded: LoadedModel | None = None
        self._result: AuditResult | None = None
        self._xml = FilePicker("XML do Erwin (*.xml)", optional=False)
        self._thesaurus = FilePicker("Planilhas (*.xls *.xlsx *.csv)", optional=True)
        self._sm077 = FilePicker("Documento Word (*.docx)", optional=True)
        self._rules_file = FilePicker("Regras YAML (*.yaml *.yml)", optional=False)
        self._model_info = QLabel("Nenhum modelo carregado.")
        self._load_button = QPushButton("Carregar modelo")
        self._target = QComboBox()
        self._scope = ScopePanel()
        self._rules = RulesPanel()
        self._results = ResultsPanel()
        self._run_button = QPushButton("Executar auditoria")
        self._progress = QProgressBar()
        self._tabs = QTabWidget()
        self._build()
        self._connect()
        self._rules_file.set_path(default_rules)
        self._refresh_actions()

    def _build(self) -> None:
        files = QWidget()
        form = QFormLayout(files)
        form.addRow("XML do Erwin:", self._xml)
        form.addRow("", self._load_button)
        form.addRow("Modelo:", self._model_info)
        form.addRow("Thesaurus:", self._thesaurus)
        form.addRow("SM077:", self._sm077)
        form.addRow("Arquivo de regras:", self._rules_file)
        scope = QWidget()
        scope_layout = QVBoxLayout(scope)
        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Banco de destino do modelo:"))
        target_row.addWidget(self._target)
        target_row.addStretch(1)
        scope_layout.addLayout(target_row)
        scope_layout.addWidget(self._scope)
        rules = QWidget()
        rules_layout = QVBoxLayout(rules)
        note = QLabel(
            "Desmarque uma regra para desativá-la nesta execução. Regras desativadas "
            "aparecem no relatório. Uma regra marcada sem a referência exigida impede a auditoria."
        )
        note.setWordWrap(True)
        rules_layout.addWidget(note)
        rules_layout.addWidget(self._rules)
        self._tabs.addTab(files, "1. Arquivos")
        self._tabs.addTab(scope, "2. Escopo")
        self._tabs.addTab(rules, "3. Regras")
        self._tabs.addTab(self._results, "4. Resultado")
        self._target.addItem("Selecione o banco de destino", "")
        for target, label in _TARGET_LABELS.items():
            self._target.addItem(label, target.value)
        self._progress.setRange(0, 1)
        self._progress.setTextVisible(False)
        bottom = QHBoxLayout()
        bottom.addWidget(self._progress, 1)
        bottom.addWidget(self._run_button)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.addWidget(self._tabs, 1)
        layout.addLayout(bottom)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Escolha o XML exportado pelo Erwin.")

    def _connect(self) -> None:
        self._load_button.clicked.connect(self._load_model)
        self._xml.changed.connect(self._refresh_actions)
        self._rules_file.changed.connect(self._load_rules)
        self._scope.area.currentIndexChanged.connect(self._refresh_actions)
        self._target.currentIndexChanged.connect(self._refresh_actions)
        self._run_button.clicked.connect(self._run)
        self._results.export_excel_requested.connect(lambda: self._export("xlsx"))
        self._results.export_pdf_requested.connect(lambda: self._export("pdf"))

    def _busy(self, message: str | None) -> None:
        busy = message is not None
        self._progress.setRange(0, 0 if busy else 1)
        self.statusBar().showMessage(message or "Pronto.")
        for widget in (self._load_button, self._run_button, self._tabs):
            widget.setEnabled(not busy)
        if not busy:
            self._refresh_actions()

    def _refresh_actions(self) -> None:
        self._load_button.setEnabled(self._xml.path() is not None)
        ready = self._loaded is not None and bool(self._scope.chosen_area())
        self._run_button.setEnabled(ready and bool(self._target.currentData()))

    def _fail(self, message: str) -> None:
        self._busy(None)
        QMessageBox.warning(self, "Não foi possível concluir", message)

    def _load_rules(self) -> None:
        path = self._rules_file.path()
        if path is None:
            return
        self._runner.start(lambda: self._workflow.load_rules(path), self._rules_loaded, self._fail)

    def _rules_loaded(self, catalog: object) -> None:
        if isinstance(catalog, RuleCatalog):
            self._rules.set_catalog(catalog)
            self.statusBar().showMessage(f"Regras versão {catalog.version} carregadas.")

    def _load_model(self) -> None:
        path = self._xml.path()
        if path is None:
            return
        self._busy("Lendo o XML. Modelos grandes podem levar cerca de um minuto...")
        self._runner.start(lambda: self._workflow.load_model(path), self._model_loaded, self._fail)

    def _model_loaded(self, loaded: object) -> None:
        if not isinstance(loaded, LoadedModel):
            return
        self._loaded = loaded
        model = loaded.model
        self._model_info.setText(
            f"{model.name} · {len(model.tables)} tabelas · "
            f"{len(model.subject_areas)} Subject Areas · Target_Server {model.target_server}"
        )
        target = target_from_erwin(model.target_server)
        self._target.setCurrentIndex(self._target.findData(target.value) if target else 0)
        self._scope.set_model(model)
        self._busy(None)
        self._tabs.setCurrentIndex(1)
        self.statusBar().showMessage("Modelo carregado. Escolha a Subject Area.")

    def _run(self) -> None:
        if self._loaded is None:
            return
        rules_path = self._rules_file.path()
        if rules_path is None:
            QMessageBox.warning(self, "Arquivo de regras", "Escolha o arquivo de regras YAML.")
            return
        selection = self._scope.selection()
        session = AuditSession(
            loaded=self._loaded,
            rules_path=rules_path,
            request=AuditRequest(
                subject_area=self._scope.chosen_area(),
                target_database=TargetDatabase(str(self._target.currentData())),
                table_ids=selection.table_ids,
                column_ids=selection.column_ids,
            ),
            thesaurus_path=self._thesaurus.path(),
            specification_path=self._sm077.path(),
            disabled_rules=self._rules.disabled_codes(),
        )
        self._busy("Executando a auditoria...")
        self._runner.start(lambda: self._workflow.run(session), self._finished, self._fail)

    def _finished(self, result: object) -> None:
        if not isinstance(result, AuditResult):
            return
        self._result = result
        names = {rule.code: rule.name for rule in result.plan.rules}
        rows = tuple(finding_row(item, names) for item in result.findings)
        counts = Counter(item.severity for item in result.findings)
        detail = ", ".join(f"{severity_label(key)} {value}" for key, value in counts.items())
        self._results.show_rows(
            rows,
            f"{len(rows)} inconsistências em {len(result.scope.tables)} tabelas"
            + (f" ({detail})" if detail else ""),
        )
        self._busy(None)
        self._tabs.setCurrentIndex(_RESULT_TAB)

    def _export(self, extension: str) -> None:
        result = self._result
        if result is None:
            return
        stamp = result.executed_at.strftime("%Y%m%d_%H%M")
        suggested = f"auditoria_{stamp}.{extension}"
        label = "Excel (*.xlsx)" if extension == "xlsx" else "PDF (*.pdf)"
        chosen, _ = QFileDialog.getSaveFileName(self, "Salvar relatório", suggested, label)
        if not chosen:
            return
        path = Path(chosen)
        writer = self._workflow.export_excel if extension == "xlsx" else self._workflow.export_pdf
        self._busy("Gerando o relatório...")
        self._runner.start(
            lambda: writer(result, path),
            lambda _: self._exported(path),
            self._fail,
        )

    def _exported(self, path: Path) -> None:
        self._busy(None)
        QMessageBox.information(self, "Relatório gerado", f"Relatório salvo em:\n{path}")

    def closeEvent(self, event: QCloseEvent) -> None:
        """Let a running task finish before the window closes."""
        self._runner.wait()
        event.accept()
