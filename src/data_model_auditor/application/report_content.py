"""Turn an audit result into the tables shown by every report format."""

from collections import Counter
from dataclasses import dataclass

from data_model_auditor.application.audit_service import AuditResult
from data_model_auditor.domain.audit_scope import AUDITED
from data_model_auditor.domain.rule_catalog import AuditRule, RuleCategory
from data_model_auditor.domain.severity import Severity
from data_model_auditor.domain.validation import ValidationFinding

SEVERITY_LABELS = {
    Severity.CRITICAL: "Crítica",
    Severity.HIGH: "Alta",
    Severity.MEDIUM: "Média",
    Severity.LOW: "Baixa",
    Severity.INFO: "Informativa",
}
CATEGORY_LABELS = {
    RuleCategory.NAMING.value: "Nomenclatura",
    RuleCategory.PREFIX.value: "Prefixo",
    RuleCategory.TABLE.value: "Tabela",
    RuleCategory.PRIMARY_KEY.value: "Chave primária",
    RuleCategory.FOREIGN_KEY.value: "Chave estrangeira",
    RuleCategory.DATA_TYPE.value: "Tipo de dado",
    RuleCategory.DEFAULT.value: "DEFAULT",
    RuleCategory.INDEX.value: "Índice",
    RuleCategory.DESCRIPTION.value: "Descrição",
}
FINDING_HEADERS = (
    "Severidade",
    "Categoria",
    "Código da regra",
    "Regra violada",
    "Subject Area",
    "Tabela",
    "Campo físico",
    "Campo lógico",
    "Inconsistência",
    "Justificativa",
    "Sugestão de correção",
    "Documento de origem",
    "Página",
    "Versão da regra",
)


@dataclass(frozen=True)
class ReportSheet:
    """One titled table of text cells."""

    title: str
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ReportContent:
    """The five sections required for the MVP reports."""

    summary: ReportSheet
    findings: ReportSheet
    tables: ReportSheet
    fields: ReportSheet
    configuration: ReportSheet

    def sheets(self) -> tuple[ReportSheet, ...]:
        """Sections in report order."""
        return (self.summary, self.findings, self.tables, self.fields, self.configuration)


def severity_label(severity: Severity) -> str:
    """Portuguese label for a severity."""
    return SEVERITY_LABELS[severity]


def category_label(category: str) -> str:
    """Portuguese label for a rule category."""
    return CATEGORY_LABELS.get(category, category)


def finding_row(finding: ValidationFinding, rule_names: dict[str, str]) -> tuple[str, ...]:
    """One finding as text cells in ``FINDING_HEADERS`` order."""
    return (
        severity_label(finding.severity),
        category_label(finding.validation_type),
        finding.rule_code,
        rule_names.get(finding.rule_code, ""),
        finding.subject_area,
        finding.table_name,
        finding.physical_field_name,
        finding.logical_field_name,
        finding.message,
        finding.justification,
        finding.correction_suggestion,
        finding.source,
        "" if finding.normative_page is None else str(finding.normative_page),
        finding.rule_version,
    )


def build_report_content(result: AuditResult) -> ReportContent:
    """Build every report section from one result."""
    rule_names = {rule.code: rule.name for rule in result.plan.rules}
    return ReportContent(
        summary=_summary(result),
        findings=ReportSheet(
            "Inconsistências",
            FINDING_HEADERS,
            tuple(finding_row(item, rule_names) for item in _ordered(result.findings)),
        ),
        tables=_tables(result),
        fields=_fields(result),
        configuration=_configuration(result),
    )


def _ordered(findings: tuple[ValidationFinding, ...]) -> list[ValidationFinding]:
    rank = {severity: index for index, severity in enumerate(Severity)}
    return sorted(
        findings,
        key=lambda item: (rank[item.severity], item.table_name, item.physical_field_name),
    )


def _summary(result: AuditResult) -> ReportSheet:
    scope = result.scope
    severities = Counter(item.severity for item in result.findings)
    categories = Counter(item.validation_type for item in result.findings)
    audited_columns = sum(1 for item in scope.columns if item.role == AUDITED)
    rows: list[tuple[str, str]] = [
        ("Modelo", result.model.name),
        ("Subject Area", scope.subject_area.name),
        ("Banco de destino", result.request.target_database.value),
        ("Data e hora", result.executed_at.strftime("%d/%m/%Y %H:%M:%S")),
        ("Versão das regras", result.plan.version),
        ("Tabelas auditadas", str(len(scope.tables))),
        ("Dependências estruturais", str(len(scope.structural_tables))),
        ("Campos auditados", str(audited_columns)),
        ("Regras executadas", str(len(result.plan.rules))),
        ("Regras desativadas", str(len(result.plan.skipped))),
        ("Total de inconsistências", str(len(result.findings))),
    ]
    rows.extend(
        (f"Severidade {severity_label(severity)}", str(severities.get(severity, 0)))
        for severity in Severity
    )
    rows.extend(
        (f"Categoria {category_label(name)}", str(total))
        for name, total in sorted(categories.items())
    )
    return ReportSheet("Resumo", ("Indicador", "Valor"), tuple(rows))


def _counts_by_table(result: AuditResult) -> Counter[str]:
    return Counter(item.table_name for item in result.findings)


def _tables(result: AuditResult) -> ReportSheet:
    counts = _counts_by_table(result)
    rows = [
        (
            table.physical_name,
            table.logical_name,
            role,
            str(len(table.columns)),
            "Sim" if table.definition.strip() else "Não",
            str(counts.get(table.physical_name, 0)) if role == "Auditada" else "",
        )
        for role, tables in (
            ("Auditada", result.scope.tables),
            ("Dependência estrutural", result.scope.structural_tables),
        )
        for table in tables
    ]
    headers = ("Tabela", "Nome lógico", "Papel", "Campos", "Descrição", "Inconsistências")
    return ReportSheet("Tabelas", headers, tuple(rows))


def _fields(result: AuditResult) -> ReportSheet:
    counts = Counter(
        (item.table_name, item.physical_field_name)
        for item in result.findings
        if item.physical_field_name
    )
    rows: list[tuple[str, ...]] = []
    for scoped in result.scope.columns:
        column = scoped.column
        table_name = result.scope.table_name(scoped.table_id)
        nullable = {True: "Sim", False: "Não", None: ""}[column.nullable]
        rows.append(
            (
                table_name,
                column.physical_name,
                column.logical_name,
                column.physical_data_type,
                nullable,
                column.default_value,
                "Sim" if column.definition.strip() else "Não",
                str(counts.get((table_name, column.physical_name), 0)),
            )
        )
    headers = (
        "Tabela",
        "Campo físico",
        "Campo lógico",
        "Tipo físico",
        "Aceita nulo",
        "DEFAULT",
        "Descrição",
        "Inconsistências",
    )
    return ReportSheet("Campos", headers, tuple(rows))


def _rule_row(rule: AuditRule, status: str) -> tuple[str, str, str]:
    detail = f"{category_label(rule.category.value)} · {severity_label(rule.severity)}"
    return (f"Regra {rule.code}", f"{status}: {rule.name}", f"{detail} · {rule.normative_source}")


def _configuration(result: AuditResult) -> ReportSheet:
    rows: list[tuple[str, str, str]] = [
        (f"Arquivo {source.role}", source.name, f"SHA-256 {source.sha256}")
        for source in result.sources
    ]
    rows.append(("Subject Area", result.scope.subject_area.name, ""))
    rows.append(("Tabelas selecionadas", _selection(result.request.table_ids), ""))
    rows.append(("Campos selecionados", _selection(result.request.column_ids), ""))
    rows.append(("Banco de destino", result.request.target_database.value, ""))
    rows.append(("Versão das regras", result.plan.version, ""))
    rows.extend(_rule_row(rule, "Executada") for rule in result.plan.rules)
    rows.extend(
        (f"Regra {item.code}", "Desativada explicitamente", category_label(item.category.value))
        for item in result.plan.skipped
    )
    return ReportSheet("Configuração", ("Item", "Valor", "Detalhe"), tuple(rows))


def _selection(ids: tuple[str, ...]) -> str:
    return f"{len(ids)} escolhidos" if ids else "Todos da Subject Area"
