"""Tests for prefix, description, and SM077 validators."""

from data_model_auditor.domain.reference_catalog import (
    DocumentedColumn,
    EntitySpecification,
    LabeledValue,
    NameClass,
    ThesaurusCatalog,
)
from data_model_auditor.domain.rule_catalog import RequiredReference, RuleCategory
from data_model_auditor.domain.validators.descriptions import DescriptionValidator
from data_model_auditor.domain.validators.prefix import PrefixValidator
from data_model_auditor.domain.validators.sm077 import Sm077Validator
from fixtures.synthetic_model import CONTEXT, column, rule, scope_of, table

_CLASSES = ThesaurusCatalog(
    entries=(),
    name_classes=(NameClass("1", "Código", "CD", "C", ""), NameClass("2", "Valor", "VR", "V", "")),
)
_SM077 = rule(
    "DESC-002",
    RuleCategory.DESCRIPTION,
    {"entity_label": "NOME DA ENTIDADE", "report_undocumented_xml_columns": True},
    reference=RequiredReference.SM077,
)


def _prefix(position: str) -> PrefixValidator:
    return PrefixValidator(
        rule("PREF-001", RuleCategory.PREFIX, {"separator": "_", "position": position}),
        _CLASSES,
    )


def test_prefix_from_the_class_sheet_is_accepted_and_others_reported() -> None:
    scope = scope_of(
        (table("t1", "T", (column("c1", "CD_CLIENTE"), column("c2", "XX_CLIENTE"))),)
    )
    findings = _prefix("first").validate(scope, CONTEXT)
    assert [item.physical_field_name for item in findings] == ["XX_CLIENTE"]
    assert "CD, VR" in findings[0].correction_suggestion


def test_prefix_position_comes_from_the_rule_file() -> None:
    scope = scope_of((table("t1", "T", (column("c1", "CLIENTE_CD"),)),))
    assert _prefix("last").validate(scope, CONTEXT) == ()
    assert len(_prefix("first").validate(scope, CONTEXT)) == 1


def test_missing_and_short_descriptions_are_reported() -> None:
    columns = (
        column("c1", "CD_A", definition=""),
        column("c2", "CD_B", definition="Curta"),
        column("c3", "CD_C", definition="Descrição completa"),
    )
    scope = scope_of((table("t1", "T", columns, definition=""),))
    plain = DescriptionValidator(rule("DESC-001", RuleCategory.DESCRIPTION))
    sized = DescriptionValidator(rule("DESC-001", RuleCategory.DESCRIPTION, {"min_length": 10}))
    assert len(plain.validate(scope, CONTEXT)) == 2
    assert len(sized.validate(scope, CONTEXT)) == 3


def _specification(entity: str, columns: tuple[DocumentedColumn, ...]) -> EntitySpecification:
    return EntitySpecification(
        fields=(LabeledValue("NOME DA ENTIDADE", entity),),
        columns=columns,
    )


def test_sm077_entity_outside_the_scope_is_reported_once() -> None:
    scope = scope_of((table("t1", "OTHER", (column("c1", "CD_X"),)),))
    spec = _specification("Nova / DBO.NOVA", ())
    findings = Sm077Validator(_SM077, spec).validate(scope, CONTEXT)
    assert len(findings) == 1
    assert findings[0].table_name == "NOVA"


def test_sm077_column_divergences() -> None:
    columns = (
        column("c1", "CD_X", "INT", nullable=False, definition="Código"),
        column("c2", "VR_Y", "DECIMAL(9,2)", nullable=True, definition="Valor"),
        column("c3", "CD_EXTRA", "INT"),
    )
    scope = scope_of((table("t1", "PARCELA", columns),))
    documented = (
        DocumentedColumn("I", "X", "CD_X", "INT NOT NULL", False, "Código"),
        DocumentedColumn("I", "Y", "VR_Y", "DECIMAL(11, 2) NOT NULL", False, "Outro texto"),
        DocumentedColumn("I", "Z", "CD_ONLY_DOC", "INT", None, ""),
    )
    spec = _specification("Parcela / DBO.PARCELA", documented)

    findings = Sm077Validator(_SM077, spec).validate(scope, CONTEXT)
    by_field = [(item.physical_field_name, item.message) for item in findings]

    assert not any(name == "CD_X" for name, _ in by_field)
    vr_y = [message for name, message in by_field if name == "VR_Y"]
    assert len(vr_y) == 3
    assert any(name == "CD_ONLY_DOC" for name, _ in by_field)
    assert any(name == "CD_EXTRA" for name, _ in by_field)
