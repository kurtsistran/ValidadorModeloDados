"""Compare the audited model with the SM077 entity specification."""

from data_model_auditor.domain.audit_scope import AuditScope
from data_model_auditor.domain.data_model import ModelColumn, ModelTable
from data_model_auditor.domain.data_type import parse_physical_type
from data_model_auditor.domain.reference_catalog import DocumentedColumn, EntitySpecification
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    FindingTarget,
    Violation,
    build_finding,
    is_active,
    parameter,
    text_parameter,
)


class Sm077Validator:
    """Report entity and column divergences between the XML and the SM077."""

    def __init__(self, rule: AuditRule | None, specification: EntitySpecification) -> None:
        self._rule = rule
        self._specification = specification

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return SM077 divergences for the documented entity."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        label = text_parameter(rule, "entity_label").casefold()
        entity = next(
            (item.value for item in self._specification.fields if item.label.casefold() == label),
            "",
        )
        physical = _physical_entity_name(entity)
        area = scope.subject_area.name
        table = next(
            (item for item in scope.tables if item.physical_name.casefold() == physical.casefold()),
            None,
        )
        if table is None:
            violation = Violation(
                f"A entidade '{entity or '(sem nome)'}' do SM077 não está no escopo auditado.",
                "A especificação descreve uma tabela que não foi encontrada na seleção.",
                "Confira a Subject Area, o nome físico ou se a tabela ainda será criada.",
            )
            return (build_finding(rule, context, FindingTarget(area, physical), violation),)
        report_extra = parameter(rule, "report_undocumented_xml_columns") is not False
        divergences = _column_divergences(area, table, self._specification, report_extra)
        return tuple(
            build_finding(rule, context, target, violation) for target, violation in divergences
        )


def _physical_entity_name(value: str) -> str:
    """``LOGICAL / SCHEMA.TABLE`` becomes ``TABLE``; a bare name is kept."""
    physical = value.split("/")[-1].strip()
    return physical.split(".")[-1].strip()


def _column_divergences(
    area: str,
    table: ModelTable,
    specification: EntitySpecification,
    report_extra: bool,
) -> list[tuple[FindingTarget, Violation]]:
    columns = {column.physical_name.casefold(): column for column in table.columns}
    documented = {item.physical_name.casefold() for item in specification.columns}
    found: list[tuple[FindingTarget, Violation]] = []
    for item in specification.columns:
        column = columns.get(item.physical_name.casefold())
        if column is None:
            target = FindingTarget(
                area, table.physical_name, item.physical_name, item.logical_name
            )
            found.append((target, _missing_in_xml(item)))
            continue
        found.extend(
            (_column_place(area, table, column), violation)
            for violation in _compare(item, column)
        )
    if report_extra:
        for key, column in columns.items():
            if key in documented:
                continue
            target = _column_place(area, table, column)
            found.append(
                (
                    target,
                    Violation(
                        f"A coluna '{column.physical_name}' não está documentada no SM077.",
                        "Toda coluna do modelo deve constar da especificação.",
                        "Inclua a coluna no SM077 ou confirme que ela não mudou.",
                    ),
                )
            )
    return found


def _column_place(area: str, table: ModelTable, column: ModelColumn) -> FindingTarget:
    return FindingTarget(area, table.physical_name, column.physical_name, column.logical_name)


def _missing_in_xml(item: DocumentedColumn) -> Violation:
    return Violation(
        f"A coluna '{item.physical_name}' do SM077 não existe no XML.",
        "A especificação documenta uma coluna ausente do modelo.",
        "Crie a coluna no modelo ou corrija o SM077.",
    )


def _compare(item: DocumentedColumn, column: ModelColumn) -> list[Violation]:
    violations: list[Violation] = []
    documented_type = parse_physical_type(item.data_type).normalized()
    model_type = parse_physical_type(column.physical_data_type).normalized()
    if documented_type and documented_type != model_type:
        violations.append(
            Violation(
                f"O tipo no SM077 é {documented_type} e no XML é {model_type}.",
                "O tipo documentado deve ser igual ao do modelo.",
                "Alinhe o tipo entre o modelo e o SM077.",
            )
        )
    known = item.nullable is not None and column.nullable is not None
    if known and item.nullable != column.nullable:
        violations.append(
            Violation(
                "A nulidade no SM077 difere da nulidade no XML.",
                "A obrigatoriedade documentada deve ser igual à do modelo.",
                "Alinhe NULL ou NOT NULL entre o modelo e o SM077.",
            )
        )
    documented_text = " ".join(item.observations.split()).casefold()
    model_text = " ".join(column.definition.split()).casefold()
    if documented_text and documented_text != model_text:
        violations.append(
            Violation(
                "A descrição no SM077 difere da descrição no XML.",
                "A descrição documentada deve ser igual à do modelo.",
                "Alinhe a descrição entre o modelo e o SM077.",
            )
        )
    return violations
