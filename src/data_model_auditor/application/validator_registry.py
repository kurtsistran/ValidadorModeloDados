"""Map rule codes from the YAML file to the validators that implement them."""

from collections.abc import Callable
from dataclasses import dataclass

from data_model_auditor.application.validation_engine import Validator
from data_model_auditor.domain.audit_scope import AuditScope
from data_model_auditor.domain.reference_catalog import EntitySpecification, ThesaurusCatalog
from data_model_auditor.domain.rule_catalog import AuditRule, RuleConfigurationError, RuleRunPlan
from data_model_auditor.domain.target_database import TargetDatabase
from data_model_auditor.domain.validators.data_types import (
    DataTypeValidator,
    DefaultValueValidator,
)
from data_model_auditor.domain.validators.descriptions import DescriptionValidator
from data_model_auditor.domain.validators.indexes import IndexValidator
from data_model_auditor.domain.validators.keys import ForeignKeyValidator, PrimaryKeyValidator
from data_model_auditor.domain.validators.naming import NamingValidator
from data_model_auditor.domain.validators.prefix import PrefixValidator
from data_model_auditor.domain.validators.sm077 import Sm077Validator
from data_model_auditor.domain.validators.tables import TableStructureValidator


@dataclass(frozen=True)
class AuditReferences:
    """Reference documents already read for one run."""

    thesaurus: ThesaurusCatalog | None = None
    specification: EntitySpecification | None = None


_Factory = Callable[[AuditRule, AuditReferences, TargetDatabase], Validator[AuditScope]]


def _thesaurus(references: AuditReferences) -> ThesaurusCatalog:
    if references.thesaurus is None:
        raise RuleConfigurationError("The thesaurus is required by an enabled rule.")
    return references.thesaurus


def _specification(references: AuditReferences) -> EntitySpecification:
    if references.specification is None:
        raise RuleConfigurationError("The SM077 is required by an enabled rule.")
    return references.specification


_FACTORIES: dict[str, _Factory] = {
    "NAME-001": lambda rule, refs, _: NamingValidator(rule, _thesaurus(refs)),
    "PREF-001": lambda rule, refs, _: PrefixValidator(rule, _thesaurus(refs)),
    "TABLE-001": lambda rule, _, __: TableStructureValidator(rule),
    "PK-001": lambda rule, _, __: PrimaryKeyValidator(rule),
    "FK-001": lambda rule, _, __: ForeignKeyValidator(rule),
    "TYPE-001": lambda rule, _, target: DataTypeValidator(rule, target),
    "DEF-001": lambda rule, _, __: DefaultValueValidator(rule),
    "IDX-001": lambda rule, _, __: IndexValidator(rule),
    "DESC-001": lambda rule, _, __: DescriptionValidator(rule),
    "DESC-002": lambda rule, refs, _: Sm077Validator(rule, _specification(refs)),
}


def supported_rule_codes() -> frozenset[str]:
    """Codes that have a validator in this version."""
    return frozenset(_FACTORIES)


def build_validators(
    plan: RuleRunPlan,
    references: AuditReferences,
    target: TargetDatabase,
) -> tuple[Validator[AuditScope], ...]:
    """Create one validator per planned rule. An unknown code stops the run."""
    validators: list[Validator[AuditScope]] = []
    for rule in plan.rules:
        factory = _FACTORIES.get(rule.code)
        if factory is None:
            raise RuleConfigurationError(f"No validator implements rule {rule.code}.")
        validators.append(factory(rule, references, target))
    return tuple(validators)
