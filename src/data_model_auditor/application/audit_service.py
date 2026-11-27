"""Run one local audit: scope, rule plan, validators, and findings."""

from dataclasses import dataclass
from datetime import datetime

from data_model_auditor.application.validation_engine import ValidationEngine
from data_model_auditor.application.validator_registry import AuditReferences, build_validators
from data_model_auditor.domain.audit_scope import AuditScope, select_audit_scope
from data_model_auditor.domain.data_model import LogicalDataModel
from data_model_auditor.domain.rule_catalog import (
    RequiredReference,
    RuleCatalog,
    RuleRunPlan,
    plan_rule_run,
)
from data_model_auditor.domain.target_database import TargetDatabase
from data_model_auditor.domain.validation import RuleContext, ValidationFinding


@dataclass(frozen=True)
class SourceFile:
    """A file used by the run, identified by name and SHA-256."""

    role: str
    name: str
    sha256: str


@dataclass(frozen=True)
class AuditRequest:
    """What the user chose for one run."""

    subject_area: str
    target_database: TargetDatabase
    table_ids: tuple[str, ...] = ()
    column_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuditResult:
    """Everything a report needs about one completed run."""

    model: LogicalDataModel
    scope: AuditScope
    plan: RuleRunPlan
    findings: tuple[ValidationFinding, ...]
    request: AuditRequest
    sources: tuple[SourceFile, ...]
    executed_at: datetime


def available_references(references: AuditReferences) -> frozenset[RequiredReference]:
    """References that were supplied for this run."""
    found: set[RequiredReference] = set()
    if references.thesaurus is not None:
        found.add(RequiredReference.THESAURUS)
    if references.specification is not None:
        found.add(RequiredReference.SM077)
    return frozenset(found)


def run_audit(
    model: LogicalDataModel,
    catalog: RuleCatalog,
    references: AuditReferences,
    request: AuditRequest,
    sources: tuple[SourceFile, ...],
    executed_at: datetime,
) -> AuditResult:
    """Validate the selected scope. Missing references stop enabled rules first."""
    scope = select_audit_scope(
        model,
        request.subject_area,
        request.table_ids,
        request.column_ids,
    )
    plan = plan_rule_run(catalog, available_references(references))
    validators = build_validators(plan, references, request.target_database)
    findings = ValidationEngine(validators).run(scope, RuleContext(rule_version=plan.version))
    return AuditResult(
        model=model,
        scope=scope,
        plan=plan,
        findings=findings,
        request=request,
        sources=sources,
        executed_at=executed_at,
    )
