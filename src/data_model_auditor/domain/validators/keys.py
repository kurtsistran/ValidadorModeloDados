"""Primary-key and foreign-key checks on the normalized model."""

from data_model_auditor.domain.audit_scope import AUDITED, AuditScope
from data_model_auditor.domain.data_model import ModelTable, key_group_kind
from data_model_auditor.domain.data_type import parse_physical_type
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    FindingTarget,
    Violation,
    build_finding,
    column_target,
    is_active,
    parameter,
    table_target,
)


class PrimaryKeyValidator:
    """Check existence, composition, and nullability of primary keys."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return primary-key findings for each audited table."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        required = parameter(rule, "require_primary_key") is True
        findings: list[ValidationFinding] = []
        for table in scope.tables:
            findings.extend(_primary_key_findings(rule, context, scope, table, required))
        return tuple(findings)


def _primary_key_findings(
    rule: AuditRule,
    context: RuleContext,
    scope: AuditScope,
    table: ModelTable,
    required: bool,
) -> list[ValidationFinding]:
    target = table_target(scope, table)
    keys = [key for key in table.key_groups if key_group_kind(key.key_group_type) == "primary"]
    if not keys:
        if not required:
            return []
        violation = Violation(
            f"A tabela '{table.physical_name}' não tem chave primária.",
            "A regra exige chave primária em toda tabela auditada.",
            "Defina a chave primária da tabela.",
        )
        return [build_finding(rule, context, target, violation)]
    columns = {column.origin_id: column for column in table.columns}
    findings: list[ValidationFinding] = []
    for key in keys:
        if not key.members:
            violation = Violation(
                f"A chave primária '{key.physical_name}' não tem colunas.",
                "Uma chave primária precisa de ao menos uma coluna.",
                "Associe as colunas que identificam a linha.",
            )
            findings.append(build_finding(rule, context, target, violation))
        for member in key.members:
            column = columns.get(member.attribute_id)
            if column is None or column.nullable is not True:
                continue
            column_place = FindingTarget(
                target.subject_area,
                target.table_name,
                column.physical_name,
                column.logical_name,
            )
            violation = Violation(
                f"A coluna '{column.physical_name}' da chave primária aceita nulo.",
                "Coluna de chave primária não pode aceitar nulo.",
                "Defina a coluna como NOT NULL.",
            )
            findings.append(build_finding(rule, context, column_place, violation))
    return findings


class ForeignKeyValidator:
    """Check that migrated columns point to an existing parent of the same type."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return foreign-key findings for audited child tables and columns."""
        rule = self._rule
        if rule is None or not is_active(rule) or scope.model is None:
            return ()
        model = scope.model
        tables = model.table_by_id()
        audited = {table.origin_id for table in scope.tables}
        structural = {table.origin_id for table in scope.structural_tables}
        findings: list[ValidationFinding] = []
        for relationship in model.relationships:
            if relationship.child_entity_id not in audited:
                continue
            if relationship.parent_entity_id in tables:
                continue
            child = tables[relationship.child_entity_id]
            violation = Violation(
                f"O relacionamento '{relationship.name}' aponta para uma tabela pai ausente.",
                "A integridade referencial exige a tabela pai no modelo.",
                "Corrija ou remova o relacionamento.",
            )
            findings.append(build_finding(rule, context, table_target(scope, child), violation))
        owners = model.column_owner_by_id()
        for scoped in scope.columns:
            parent_id = scoped.column.parent_attribute_id
            if scoped.role != AUDITED or not parent_id:
                continue
            target = column_target(scope, scoped)
            owner = owners.get(parent_id)
            if owner is None:
                violation = Violation(
                    f"A coluna '{scoped.column.physical_name}' migra de uma coluna ausente.",
                    "A chave estrangeira precisa da coluna de origem.",
                    "Recrie o relacionamento a partir da tabela pai.",
                )
                findings.append(build_finding(rule, context, target, violation))
                continue
            parent_table, parent_column = owner
            child_type = parse_physical_type(scoped.column.physical_data_type).normalized()
            parent_type = parse_physical_type(parent_column.physical_data_type).normalized()
            if child_type == parent_type:
                continue
            note = (
                " A tabela pai está fora da seleção e foi consultada como dependência estrutural."
                if parent_table.origin_id in structural
                else ""
            )
            violation = Violation(
                f"O tipo {child_type} difere de {parent_type} em "
                f"{parent_table.physical_name}.{parent_column.physical_name}.",
                "Coluna de chave estrangeira deve ter o mesmo tipo da origem." + note,
                f"Use o tipo {parent_type}.",
            )
            findings.append(build_finding(rule, context, target, violation))
        return tuple(findings)
