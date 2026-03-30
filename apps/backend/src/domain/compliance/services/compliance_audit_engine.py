"""
Compliance Audit Engine.

Deep-check engine that evaluates AI models against regulatory framework
requirements based on declared model context attributes. Returns gap
analysis with severity ratings and actionable recommendations.

Covers: EU AI Act, GDPR, India DPDP Act, ISO 42001, NIST AI RMF.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

from core.base_service import AsyncBaseService
from core.container import service, ServiceLifetime
from core.interfaces import ILogger

logger = logging.getLogger("fairmind.compliance_audit_engine")

CheckFn = Callable[[dict], Tuple[bool, str, str]]


@dataclass
class Requirement:
    id: str
    description: str
    severity: str  # critical | major | minor | info
    check: CheckFn


@dataclass
class FrameworkSpec:
    key: str
    name: str
    requirements: list[Requirement] = field(default_factory=list)


@dataclass
class GapItem:
    framework: str
    requirement_id: str
    requirement: str
    severity: str
    finding: str
    recommendation: str


@dataclass
class FrameworkReport:
    framework: str
    compliant: bool
    score: float
    checks_passed: int
    checks_total: int
    gaps: list[GapItem]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ctx_has(ctx: dict, *keys: str) -> bool:
    mc = ctx.get("model_context") or {}
    return all(k in mc for k in keys)


# ---------------------------------------------------------------------------
# EU AI Act requirements
# ---------------------------------------------------------------------------

def _eu_risk_classification(ctx: dict) -> Tuple[bool, str, str]:
    if ctx.get("risk_level"):
        return True, "Risk level declared.", ""
    return False, "No risk level classification provided.", "Classify the AI system risk level per EU AI Act Article 6."


def _eu_transparency(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "transparency_measures"):
        return True, "Transparency measures documented.", ""
    return False, "No transparency measures documented.", "Document how users are informed they are interacting with AI (Article 52)."


def _eu_human_oversight(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "human_oversight"):
        return True, "Human oversight mechanisms described.", ""
    return False, "Human oversight not documented.", "Describe human oversight mechanisms per Article 14."


def _eu_data_governance(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "training_data_governance"):
        return True, "Training data governance documented.", ""
    return False, "Training data governance not documented.", "Document data governance practices per Article 10."


def _eu_technical_documentation(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "technical_documentation"):
        return True, "Technical documentation available.", ""
    return False, "Technical documentation missing.", "Provide technical documentation per Annex IV."


def _eu_record_keeping(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "logging_capabilities"):
        return True, "Automatic logging capabilities described.", ""
    return False, "No logging capabilities documented.", "Implement automatic event logging per Article 12."


EU_AI_ACT = FrameworkSpec(
    key="eu_ai_act",
    name="EU AI Act",
    requirements=[
        Requirement("EU-1", "Risk classification", "critical", _eu_risk_classification),
        Requirement("EU-2", "Transparency obligations", "major", _eu_transparency),
        Requirement("EU-3", "Human oversight", "major", _eu_human_oversight),
        Requirement("EU-4", "Data governance", "major", _eu_data_governance),
        Requirement("EU-5", "Technical documentation", "minor", _eu_technical_documentation),
        Requirement("EU-6", "Record keeping / logging", "minor", _eu_record_keeping),
    ],
)


# ---------------------------------------------------------------------------
# GDPR requirements
# ---------------------------------------------------------------------------

def _gdpr_lawful_basis(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "lawful_basis"):
        return True, "Lawful basis for processing documented.", ""
    return False, "Lawful basis not specified.", "Identify lawful basis under Article 6 GDPR."


def _gdpr_dpia(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "dpia_conducted"):
        return True, "DPIA completed.", ""
    return False, "No DPIA conducted.", "Conduct a Data Protection Impact Assessment per Article 35."


def _gdpr_data_minimisation(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "data_minimisation"):
        return True, "Data minimisation measures documented.", ""
    return False, "Data minimisation not documented.", "Document data minimisation practices per Article 5(1)(c)."


def _gdpr_rights(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "data_subject_rights"):
        return True, "Data subject rights processes documented.", ""
    return False, "Data subject rights processes not documented.", "Implement processes for data subject rights (Articles 15-22)."


def _gdpr_automated_decisions(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "automated_decision_safeguards"):
        return True, "Automated decision-making safeguards in place.", ""
    return False, "No safeguards for automated decision-making.", "Implement safeguards per Article 22 for automated decisions."


GDPR = FrameworkSpec(
    key="gdpr",
    name="GDPR",
    requirements=[
        Requirement("GDPR-1", "Lawful basis for processing", "critical", _gdpr_lawful_basis),
        Requirement("GDPR-2", "Data Protection Impact Assessment", "critical", _gdpr_dpia),
        Requirement("GDPR-3", "Data minimisation", "major", _gdpr_data_minimisation),
        Requirement("GDPR-4", "Data subject rights", "major", _gdpr_rights),
        Requirement("GDPR-5", "Automated decision-making safeguards", "major", _gdpr_automated_decisions),
    ],
)


# ---------------------------------------------------------------------------
# India DPDP Act requirements
# ---------------------------------------------------------------------------

def _dpdp_consent(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "consent_mechanism"):
        return True, "Consent mechanism documented.", ""
    return False, "No consent mechanism documented.", "Implement consent mechanisms per Section 6 DPDP Act."


def _dpdp_purpose_limitation(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "purpose_limitation"):
        return True, "Purpose limitation documented.", ""
    return False, "Purpose limitation not documented.", "Document purpose limitation per Section 4 DPDP Act."


def _dpdp_data_principal_rights(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "data_principal_rights"):
        return True, "Data principal rights processes documented.", ""
    return False, "Data principal rights not addressed.", "Implement data principal rights per Chapter III DPDP Act."


def _dpdp_breach_notification(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "breach_notification"):
        return True, "Breach notification process documented.", ""
    return False, "No breach notification process.", "Establish breach notification process per Section 8 DPDP Act."


DPDP_ACT = FrameworkSpec(
    key="dpdp_act",
    name="India DPDP Act",
    requirements=[
        Requirement("DPDP-1", "Consent mechanism", "critical", _dpdp_consent),
        Requirement("DPDP-2", "Purpose limitation", "major", _dpdp_purpose_limitation),
        Requirement("DPDP-3", "Data principal rights", "major", _dpdp_data_principal_rights),
        Requirement("DPDP-4", "Breach notification", "major", _dpdp_breach_notification),
    ],
)


# ---------------------------------------------------------------------------
# ISO 42001 requirements
# ---------------------------------------------------------------------------

def _iso_ai_policy(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "ai_policy"):
        return True, "AI management policy documented.", ""
    return False, "No AI management policy.", "Establish an AI management system policy per ISO 42001 Clause 5."


def _iso_risk_assessment(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "risk_assessment"):
        return True, "AI risk assessment completed.", ""
    return False, "No AI risk assessment documented.", "Conduct AI risk assessment per ISO 42001 Clause 6.1."


def _iso_objectives(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "ai_objectives"):
        return True, "AI objectives defined.", ""
    return False, "AI objectives not defined.", "Define measurable AI objectives per ISO 42001 Clause 6.2."


def _iso_performance_eval(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "performance_evaluation"):
        return True, "Performance evaluation process documented.", ""
    return False, "No performance evaluation process.", "Implement performance evaluation per ISO 42001 Clause 9."


def _iso_continual_improvement(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "continual_improvement"):
        return True, "Continual improvement process documented.", ""
    return False, "No continual improvement process.", "Establish continual improvement per ISO 42001 Clause 10."


ISO_42001 = FrameworkSpec(
    key="iso_42001",
    name="ISO 42001",
    requirements=[
        Requirement("ISO-1", "AI management policy", "critical", _iso_ai_policy),
        Requirement("ISO-2", "AI risk assessment", "critical", _iso_risk_assessment),
        Requirement("ISO-3", "AI objectives", "major", _iso_objectives),
        Requirement("ISO-4", "Performance evaluation", "minor", _iso_performance_eval),
        Requirement("ISO-5", "Continual improvement", "minor", _iso_continual_improvement),
    ],
)


# ---------------------------------------------------------------------------
# NIST AI RMF requirements
# ---------------------------------------------------------------------------

def _nist_govern(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "governance_structure"):
        return True, "AI governance structure documented.", ""
    return False, "No governance structure documented.", "Establish governance per NIST AI RMF GOVERN function."


def _nist_map(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "risk_mapping"):
        return True, "AI risk mapping completed.", ""
    return False, "Risk mapping not completed.", "Map AI risks per NIST AI RMF MAP function."


def _nist_measure(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "risk_metrics"):
        return True, "Risk metrics defined.", ""
    return False, "No risk metrics defined.", "Define risk metrics per NIST AI RMF MEASURE function."


def _nist_manage(ctx: dict) -> Tuple[bool, str, str]:
    if _ctx_has(ctx, "risk_management_plan"):
        return True, "Risk management plan in place.", ""
    return False, "No risk management plan.", "Create risk management plan per NIST AI RMF MANAGE function."


NIST_AI_RMF = FrameworkSpec(
    key="nist_ai_rmf",
    name="NIST AI RMF",
    requirements=[
        Requirement("NIST-1", "GOVERN function", "critical", _nist_govern),
        Requirement("NIST-2", "MAP function", "major", _nist_map),
        Requirement("NIST-3", "MEASURE function", "major", _nist_measure),
        Requirement("NIST-4", "MANAGE function", "major", _nist_manage),
    ],
)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

FRAMEWORK_REGISTRY: Dict[str, FrameworkSpec] = {
    spec.key: spec
    for spec in [EU_AI_ACT, GDPR, DPDP_ACT, ISO_42001, NIST_AI_RMF]
}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

@service(lifetime=ServiceLifetime.SINGLETON)
class ComplianceAuditEngine(AsyncBaseService):
    """
    Deep compliance audit engine.

    Evaluates AI model metadata against regulatory requirements and produces
    per-framework scores, gap lists, and actionable recommendations.
    """

    def __init__(self, logger_instance: Optional[ILogger] = None):
        super().__init__(logger_instance)

    async def run_audit(
        self,
        frameworks: List[str],
        risk_level: Optional[str],
        model_context: Optional[Dict],
    ) -> Tuple[List[FrameworkReport], List[GapItem]]:
        """Run compliance checks for the requested frameworks."""
        self._log_operation("run_audit", frameworks=frameworks)

        ctx = {
            "risk_level": risk_level,
            "model_context": model_context or {},
        }

        reports: List[FrameworkReport] = []
        all_gaps: List[GapItem] = []

        for fw_key in frameworks:
            spec = FRAMEWORK_REGISTRY.get(fw_key)
            if spec is None:
                logger.warning(f"Unknown framework requested: {fw_key}")
                continue

            gaps: List[GapItem] = []
            passed = 0

            for req in spec.requirements:
                ok, finding, recommendation = req.check(ctx)
                if ok:
                    passed += 1
                else:
                    gap = GapItem(
                        framework=fw_key,
                        requirement_id=req.id,
                        requirement=req.description,
                        severity=req.severity,
                        finding=finding,
                        recommendation=recommendation,
                    )
                    gaps.append(gap)
                    all_gaps.append(gap)

            total = len(spec.requirements)
            score = passed / total if total > 0 else 0.0

            reports.append(FrameworkReport(
                framework=fw_key,
                compliant=len(gaps) == 0,
                score=round(score, 3),
                checks_passed=passed,
                checks_total=total,
                gaps=gaps,
            ))

        return reports, all_gaps

    async def generate_report(
        self,
        audit_id: str,
        model_name: str,
        model_version: Optional[str],
        risk_level: Optional[str],
        reports: List[FrameworkReport],
    ) -> Dict:
        """Build a serialisable audit report dict."""
        overall_score = (
            sum(r.score for r in reports) / len(reports) if reports else 0.0
        )
        overall_compliant = all(r.compliant for r in reports)

        return {
            "audit_id": audit_id,
            "model_name": model_name,
            "model_version": model_version,
            "overall_compliant": overall_compliant,
            "overall_score": round(overall_score, 3),
            "risk_level": risk_level,
            "framework_results": [
                {
                    "framework": r.framework,
                    "framework_name": FRAMEWORK_REGISTRY[r.framework].name
                    if r.framework in FRAMEWORK_REGISTRY
                    else r.framework,
                    "compliant": r.compliant,
                    "score": r.score,
                    "checks_passed": r.checks_passed,
                    "checks_total": r.checks_total,
                    "gaps": [
                        {
                            "framework": g.framework,
                            "requirement_id": g.requirement_id,
                            "requirement": g.requirement,
                            "severity": g.severity,
                            "finding": g.finding,
                            "recommendation": g.recommendation,
                        }
                        for g in r.gaps
                    ],
                }
                for r in reports
            ],
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def list_frameworks(self) -> List[Dict]:
        """Return metadata about all supported frameworks."""
        return [
            {
                "key": spec.key,
                "name": spec.name,
                "requirement_count": len(spec.requirements),
            }
            for spec in FRAMEWORK_REGISTRY.values()
        ]
