"""Data-type and DEFAULT checks for the selected target database."""

import re

from data_model_auditor.domain.audit_scope import AUDITED, AuditScope
from data_model_auditor.domain.data_type import PhysicalType, parse_physical_type
from data_model_auditor.domain.rule_catalog import AuditRule
from data_model_auditor.domain.target_database import TargetDatabase
from data_model_auditor.domain.validation import RuleContext, ValidationFinding
from data_model_auditor.domain.validators.findings import (
    Violation,
    build_finding,
    column_target,
    is_active,
    list_parameter,
)

_NUMBER = re.compile(r"^[+-]?\d+(\.\d+)?$")
_QUOTED = re.compile(r"^N?'.*'$", re.DOTALL)


class DataTypeValidator:
    """Check type names, lengths, precision, and scale for the destination."""

    def __init__(self, rule: AuditRule | None, target: TargetDatabase) -> None:
        self._rule = rule
        self._target = target

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return a finding for each audited column with an invalid type."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        allowed = list_parameter(rule, f"{self._target.value}_types")
        sized = list_parameter(rule, "length_required_types")
        scaled = list_parameter(rule, "precision_scale_types")
        findings: list[ValidationFinding] = []
        for scoped in scope.columns:
            if scoped.role != AUDITED:
                continue
            physical = parse_physical_type(scoped.column.physical_data_type)
            violation = _type_violation(physical, allowed, sized, scaled, self._target)
            if violation is not None:
                findings.append(
                    build_finding(rule, context, column_target(scope, scoped), violation)
                )
        return tuple(findings)


def _type_violation(
    physical: PhysicalType,
    allowed: frozenset[str],
    sized: frozenset[str],
    scaled: frozenset[str],
    target: TargetDatabase,
) -> Violation | None:
    if not physical.base:
        return Violation(
            "A coluna não tem tipo físico.",
            "Toda coluna precisa de um tipo no banco de destino.",
            "Informe o tipo físico.",
        )
    if physical.base not in allowed:
        return Violation(
            f"O tipo {physical.base} não pertence ao banco {target.value}.",
            "O tipo precisa existir no banco de destino escolhido.",
            "Use um tipo equivalente do banco de destino.",
        )
    if physical.base in sized and not physical.arguments:
        return Violation(
            f"O tipo {physical.normalized()} não informa o tamanho.",
            "Este tipo exige tamanho declarado.",
            f"Informe o tamanho, por exemplo {physical.base}(n).",
        )
    if physical.base in scaled and len(physical.arguments) == 2:
        precision, scale = physical.arguments
        if precision.isdigit() and scale.isdigit() and int(scale) > int(precision):
            return Violation(
                f"A escala de {physical.normalized()} é maior que a precisão.",
                "A escala não pode exceder a precisão.",
                "Ajuste precisão e escala.",
            )
    return None


class DefaultValueValidator:
    """Check that a DEFAULT is compatible with the type and nullability."""

    def __init__(self, rule: AuditRule | None) -> None:
        self._rule = rule

    def validate(
        self,
        scope: AuditScope,
        context: RuleContext,
    ) -> tuple[ValidationFinding, ...]:
        """Return a finding for each audited DEFAULT that cannot hold."""
        rule = self._rule
        if rule is None or not is_active(rule):
            return ()
        numeric = list_parameter(rule, "numeric_types")
        findings: list[ValidationFinding] = []
        for scoped in scope.columns:
            value = _unwrap(scoped.column.default_value)
            if scoped.role != AUDITED or not value:
                continue
            violation = _default_violation(
                value,
                parse_physical_type(scoped.column.physical_data_type),
                scoped.column.nullable,
                numeric,
            )
            if violation is not None:
                findings.append(
                    build_finding(rule, context, column_target(scope, scoped), violation)
                )
        return tuple(findings)


def _unwrap(value: str) -> str:
    text = value.strip()
    while text.startswith("(") and text.endswith(")"):
        text = text[1:-1].strip()
    return text


def _default_violation(
    value: str,
    physical: PhysicalType,
    nullable: bool | None,
    numeric: frozenset[str],
) -> Violation | None:
    if value.upper() == "NULL" and nullable is False:
        return Violation(
            "O DEFAULT é NULL em uma coluna NOT NULL.",
            "Uma coluna obrigatória não pode receber nulo por padrão.",
            "Informe um valor padrão válido ou remova o DEFAULT.",
        )
    if physical.base in numeric and _QUOTED.match(value):
        inner = value.lstrip("N")[1:-1].strip()
        if not _NUMBER.match(inner):
            return Violation(
                f"O DEFAULT {value} não é numérico para o tipo {physical.normalized()}.",
                "O valor padrão precisa ser compatível com o tipo da coluna.",
                "Use um valor numérico.",
            )
    return None
