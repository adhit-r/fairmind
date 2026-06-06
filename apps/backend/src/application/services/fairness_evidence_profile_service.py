"""
FairMind AIBOM fairness evidence profile generator.

This service adapts existing FairMind AIBOM, bias test, evidence, remediation,
and review records into the research schema under
research/aibom-fairness-evidence/schema/aibom_fairness_evidence.schema.json.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Mapping


class FairnessEvidenceProfileService:
    """Generate reviewer-facing fairness evidence profiles from FairMind records."""

    PROFILE_VERSION = "0.1.0"

    _VALID_COMPONENT_TYPES = {
        "dataset",
        "model",
        "embedding",
        "preprocessing",
        "evaluation_set",
        "remediation",
        "monitor",
        "report",
    }

    _VALID_EVIDENCE_STATES = {
        "unknown",
        "missing",
        "simulated",
        "stale",
        "current",
        "reviewed",
        "not_applicable",
    }

    _VALID_SEVERITIES = {
        "low",
        "medium",
        "high",
        "critical",
        "unknown",
    }

    _SEVERITY_RANK = {
        "low": 1,
        "medium": 2,
        "high": 3,
        "critical": 4,
    }

    _SOURCE_SERVICES = [
        {
            "path": "apps/backend/src/application/services/ai_bom_service.py",
            "role": "AIBOM component lineage and risk/compliance status",
        },
        {
            "path": "apps/backend/src/application/services/real_ai_bom_service.py",
            "role": "Database-backed AIBOM document and component persistence",
        },
        {
            "path": "apps/backend/src/application/services/automated_evidence_collector.py",
            "role": "Evidence categories for bias, monitoring, documentation, and audit logging",
        },
        {
            "path": "apps/backend/src/application/services/compliance_mapper.py",
            "role": "Regulatory control and evidence mapping",
        },
        {
            "path": "apps/backend/src/application/services/india_bias_detection_service.py",
            "role": "India-specific protected-attribute and subgroup fairness evidence",
        },
        {
            "path": "apps/backend/src/application/services/modern_llm_bias_service.py",
            "role": "Modern bias tests, monitoring, and human-in-loop evaluation",
        },
    ]

    def generate_profile(
        self,
        *,
        bom_document: Mapping[str, Any] | Any,
        bias_results: Mapping[str, Mapping[str, Any]] | None = None,
        evidence_records: Mapping[str, Mapping[str, Any]] | None = None,
        remediation_records: Mapping[str, list[Mapping[str, Any]]] | None = None,
        review_state: Mapping[str, Any] | None = None,
        generated_at: datetime | None = None,
        generation_mode: str = "fairmind_runtime_export",
    ) -> dict[str, Any]:
        """Generate a fairness evidence profile document.

        Inputs are intentionally mapping-shaped so callers can pass Pydantic
        model dumps, database rows serialized to dicts, or integration payloads
        without coupling this service to one storage layer.
        """

        bias_results = bias_results or {}
        evidence_records = evidence_records or {}
        remediation_records = remediation_records or {}
        generated_at = generated_at or datetime.now(timezone.utc)

        components = []
        for raw_component in self._get(bom_document, "components", default=[]):
            component_id = self._component_id(raw_component)
            component_evidence = dict(evidence_records.get(component_id, {}))
            component_bias = dict(bias_results.get(component_id, {}))
            component_remediations = list(remediation_records.get(component_id, []))
            components.append(
                self._build_component(
                    raw_component=raw_component,
                    component_id=component_id,
                    evidence=component_evidence,
                    bias_result=component_bias,
                    remediation_history=component_remediations,
                )
            )

        system_name = self._system_name(bom_document)
        review_summary = self._review_summary(review_state)

        return {
            "profile_id": f"fairmind-{self._slug(system_name)}-fairness-profile",
            "profile_version": self.PROFILE_VERSION,
            "bom_ref": str(self._get(bom_document, "id", default="unknown-bom")),
            "system_name": system_name,
            "system_domain": str(
                self._get(bom_document, "system_domain", default="fairmind_governance")
            ),
            "generated_at": self._isoformat(generated_at),
            "fairmind_context": {
                "platform_name": "FairMind",
                "generation_mode": generation_mode,
                "source_services": self._SOURCE_SERVICES,
                "evidence_boundary": (
                    "Generated from FairMind AIBOM, bias, evidence, remediation, "
                    "and review records. Missing inputs are explicit unknown risk."
                ),
            },
            "components": components,
            "risk_summary": self._aggregate_risk_summary(components),
            "review_summary": review_summary,
            "limitations": [
                "Profile quality depends on available FairMind evidence records.",
                "Missing evidence is represented as unknown risk, not low risk.",
                "Simulated evidence is not upgraded to validated evidence.",
            ],
        }

    def _build_component(
        self,
        *,
        raw_component: Mapping[str, Any] | Any,
        component_id: str,
        evidence: dict[str, Any],
        bias_result: dict[str, Any],
        remediation_history: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        protected_attributes = list(evidence.get("protected_attributes_tested") or [])
        subgroup_coverage = self._subgroup_coverage(evidence.get("subgroup_coverage"))
        fairness_metrics = self._normalise_fairness_metrics(evidence.get("fairness_metrics"))
        bias_tests_run = self._normalise_bias_tests(evidence.get("bias_tests_run"))
        known_bias_risks = self._normalise_bias_risks(
            bias_result.get("known_bias_risks") or evidence.get("known_bias_risks")
        )
        remediations = self._normalise_remediations(remediation_history)
        evidence_refs = list(evidence.get("evidence_refs") or [])
        evidence_freshness = self._evidence_freshness(evidence.get("evidence_freshness"))
        regulatory_mapping = self._normalise_regulatory_mapping(
            evidence.get("regulatory_mapping")
        )
        unknowns = self._unknowns(
            protected_attributes=protected_attributes,
            subgroup_coverage=subgroup_coverage,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            evidence_refs=evidence_refs,
            evidence_freshness=evidence_freshness,
        )
        validation_state = self._validation_state(
            evidence_freshness=evidence_freshness,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=known_bias_risks,
            regulatory_mapping=regulatory_mapping,
            remediations=remediations,
        )
        component_type, type_unknown = self._component_type(raw_component)
        if type_unknown:
            unknowns.append(type_unknown)

        risk_summary = self._component_risk_summary(
            unknowns=unknowns,
            known_bias_risks=known_bias_risks,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            regulatory_mapping=regulatory_mapping,
            evidence_freshness=evidence_freshness,
            remediations=remediations,
        )

        metadata = self._metadata(raw_component)
        review_status = str(
            evidence.get("review_status")
            or metadata.get("review_status")
            or ("review_required" if unknowns else "pending")
        )
        reviewer = (
            evidence.get("reviewer")
            or evidence.get("reviewed_by")
            or metadata.get("reviewer")
            or metadata.get("reviewed_by")
        )
        reviewer_evidence = self._reviewer_evidence_fields(
            component_id=component_id,
            component_type=component_type,
            evidence=evidence,
            evidence_refs=evidence_refs,
            protected_attributes=protected_attributes,
            subgroup_coverage=subgroup_coverage,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=known_bias_risks,
            remediations=remediations,
            regulatory_mapping=regulatory_mapping,
            evidence_freshness=evidence_freshness,
            review_status=review_status,
            reviewer=reviewer,
        )

        return {
            "component_id": component_id,
            "component_type": component_type,
            "component_name": str(
                self._get(raw_component, "name", default=self._get(raw_component, "component_name", default=component_id))
            ),
            "version": str(self._get(raw_component, "version", default="unknown")),
            "upstream_components": list(
                self._get(raw_component, "dependencies", default=metadata.get("upstream_components", []))
                or []
            ),
            "downstream_components": list(metadata.get("downstream_components", [])),
            "protected_attributes_tested": protected_attributes,
            "subgroup_coverage": subgroup_coverage,
            "fairness_metrics": fairness_metrics,
            "bias_tests_run": bias_tests_run,
            "known_bias_risks": known_bias_risks,
            "remediation_history": remediations,
            "validation_state": validation_state,
            "evidence_refs": evidence_refs,
            "evidence_freshness": evidence_freshness,
            "review_status": review_status,
            "regulatory_mapping": regulatory_mapping,
            "unknowns": unknowns,
            "risk_summary": risk_summary,
            **reviewer_evidence,
        }

    def _system_name(self, bom_document: Mapping[str, Any] | Any) -> str:
        for key in ("system_name", "project_name", "name"):
            value = self._get(bom_document, key, default=None)
            if value:
                return str(value)
        return "FairMind System"

    def _component_id(self, component: Mapping[str, Any] | Any) -> str:
        for key in ("component_id", "id", "name"):
            value = self._get(component, key, default=None)
            if value:
                return str(value)
        return "unknown-component"

    def _component_type(self, component: Mapping[str, Any] | Any) -> tuple[str, str | None]:
        metadata = self._metadata(component)
        raw_type = str(metadata.get("profile_component_type") or self._get(component, "type", default="model"))
        raw_type = raw_type.lower()
        if raw_type in self._VALID_COMPONENT_TYPES:
            return raw_type, None
        return (
            "model",
            f"Original AIBOM component type '{raw_type}' does not map directly to the profile schema.",
        )

    def _metadata(self, component: Mapping[str, Any] | Any) -> Mapping[str, Any]:
        metadata = self._get(component, "component_metadata", default={})
        return metadata if isinstance(metadata, Mapping) else {}

    def _subgroup_coverage(self, coverage: Any) -> dict[str, Any]:
        if isinstance(coverage, Mapping):
            return {
                "evaluated_groups": list(coverage.get("evaluated_groups") or []),
                "missing_groups": list(coverage.get("missing_groups") or []),
                "coverage_notes": str(coverage.get("coverage_notes") or ""),
            }
        return {
            "evaluated_groups": [],
            "missing_groups": [],
            "coverage_notes": "No subgroup coverage evidence attached.",
        }

    def _normalise_fairness_metrics(self, metrics: Any) -> list[dict[str, Any]]:
        normalised = []
        for metric in metrics or []:
            if not isinstance(metric, Mapping):
                continue
            normalised.append(
                {
                    "metric": str(metric.get("metric") or "unnamed_metric"),
                    "value": metric.get("value"),
                    "threshold": metric.get("threshold"),
                    "affected_groups": list(metric.get("affected_groups") or []),
                    "evidence_state": self._evidence_state(metric.get("evidence_state")),
                }
            )
        return normalised

    def _normalise_bias_tests(self, tests: Any) -> list[dict[str, Any]]:
        normalised = []
        for test in tests or []:
            if not isinstance(test, Mapping):
                continue
            normalised.append(
                {
                    "test_name": str(test.get("test_name") or "unnamed_test"),
                    "test_type": str(test.get("test_type") or "unknown"),
                    "result": str(test.get("result") or ""),
                    "evidence_state": self._evidence_state(test.get("evidence_state")),
                    "evidence_ref": str(test.get("evidence_ref") or ""),
                }
            )
        return normalised

    def _normalise_bias_risks(self, risks: Any) -> list[dict[str, Any]]:
        normalised = []
        for index, risk in enumerate(risks or [], start=1):
            if not isinstance(risk, Mapping):
                continue
            normalised.append(
                {
                    "risk_id": str(risk.get("risk_id") or f"fairmind-risk-{index}"),
                    "description": str(risk.get("description") or "Unspecified fairness risk."),
                    "affected_groups": list(risk.get("affected_groups") or []),
                    "severity": self._severity(risk.get("severity")),
                    "evidence_state": self._evidence_state(risk.get("evidence_state")),
                }
            )
        return normalised

    def _normalise_remediations(self, remediations: Any) -> list[dict[str, Any]]:
        normalised = []
        for index, remediation in enumerate(remediations or [], start=1):
            if not isinstance(remediation, Mapping):
                continue
            normalised.append(
                {
                    "remediation_id": str(
                        remediation.get("remediation_id") or f"fairmind-remediation-{index}"
                    ),
                    "description": str(
                        remediation.get("description") or "Unspecified remediation."
                    ),
                    "status": str(remediation.get("status") or "unknown"),
                    "validation_state": self._remediation_validation_state(
                        remediation.get("validation_state")
                    ),
                    "evidence_ref": str(remediation.get("evidence_ref") or ""),
                }
            )
        return normalised

    def _normalise_regulatory_mapping(self, mappings: Any) -> list[dict[str, Any]]:
        normalised = []
        for mapping in mappings or []:
            if not isinstance(mapping, Mapping):
                continue
            normalised.append(
                {
                    "framework": str(mapping.get("framework") or "unknown"),
                    "control": str(mapping.get("control") or "unknown"),
                    "claim": str(mapping.get("claim") or "Unspecified regulatory claim."),
                    "evidence_state": self._evidence_state(mapping.get("evidence_state")),
                }
            )
        return normalised

    def _evidence_freshness(self, freshness: Any) -> dict[str, Any]:
        if isinstance(freshness, Mapping):
            return {
                "last_updated": freshness.get("last_updated"),
                "expires_at": freshness.get("expires_at"),
                "staleness_rule": str(
                    freshness.get("staleness_rule") or "No staleness rule provided."
                ),
                "evidence_state": self._evidence_state(freshness.get("evidence_state")),
            }
        return {
            "last_updated": None,
            "expires_at": None,
            "staleness_rule": "No evidence freshness record attached.",
            "evidence_state": "unknown",
        }

    def _unknowns(
        self,
        *,
        protected_attributes: list[str],
        subgroup_coverage: Mapping[str, Any],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        evidence_refs: list[str],
        evidence_freshness: Mapping[str, Any],
    ) -> list[str]:
        unknowns = []
        if not protected_attributes:
            unknowns.append("No protected attributes tested.")
        if not subgroup_coverage.get("evaluated_groups"):
            unknowns.append("No subgroup coverage evidence attached.")
        if not fairness_metrics:
            unknowns.append("No fairness metrics attached.")
        if not bias_tests_run:
            unknowns.append("No bias tests attached.")
        if not evidence_refs:
            unknowns.append("No evidence references attached.")
        if evidence_freshness.get("evidence_state") in {"unknown", "missing"}:
            unknowns.append("Evidence freshness is unknown.")
        return unknowns

    def _validation_state(
        self,
        *,
        evidence_freshness: Mapping[str, Any],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        known_bias_risks: list[Mapping[str, Any]],
        regulatory_mapping: list[Mapping[str, Any]],
        remediations: list[Mapping[str, Any]],
    ) -> str:
        states = self._component_evidence_states(
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=known_bias_risks,
            regulatory_mapping=regulatory_mapping,
            evidence_freshness=evidence_freshness,
        )
        remediation_states = {
            remediation.get("validation_state") for remediation in remediations
        }
        if "reviewed" in states or "reviewed" in remediation_states:
            return "reviewed"
        if "current" in states:
            return "validated"
        if "simulated" in states or "simulated" in remediation_states:
            return "simulated"
        if "retrained" in remediation_states:
            return "retrained"
        return "untested"

    def _component_risk_summary(
        self,
        *,
        unknowns: list[str],
        known_bias_risks: list[Mapping[str, Any]],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        regulatory_mapping: list[Mapping[str, Any]],
        evidence_freshness: Mapping[str, Any],
        remediations: list[Mapping[str, Any]],
    ) -> dict[str, Any]:
        evidence_states = self._component_evidence_states(
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=known_bias_risks,
            regulatory_mapping=regulatory_mapping,
            evidence_freshness=evidence_freshness,
        )
        remediations_simulated = sum(
            1 for remediation in remediations if remediation.get("validation_state") == "simulated"
        )
        severity = self._overall_component_severity(known_bias_risks, unknowns)
        key_risks = [
            str(risk.get("description"))
            for risk in known_bias_risks
            if risk.get("description")
        ]
        if unknowns and not key_risks:
            key_risks = ["unknown fairness evidence"]

        return {
            "overall_severity": severity,
            "key_risks": key_risks,
            "unknown_count": len(unknowns),
            "stale_evidence_count": evidence_states.count("stale"),
            "simulated_evidence_count": evidence_states.count("simulated")
            + remediations_simulated,
            "reviewer_action": self._reviewer_action(severity, unknowns),
        }

    def _reviewer_evidence_fields(
        self,
        *,
        component_id: str,
        component_type: str,
        evidence: Mapping[str, Any],
        evidence_refs: list[str],
        protected_attributes: list[str],
        subgroup_coverage: Mapping[str, Any],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        known_bias_risks: list[Mapping[str, Any]],
        remediations: list[Mapping[str, Any]],
        regulatory_mapping: list[Mapping[str, Any]],
        evidence_freshness: Mapping[str, Any],
        review_status: str,
        reviewer: Any,
    ) -> dict[str, Any]:
        gap_type, reason, fault, action = self._component_evidence_gap(
            component_type=component_type,
            evidence=evidence,
            protected_attributes=protected_attributes,
            subgroup_coverage=subgroup_coverage,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=known_bias_risks,
            remediations=remediations,
            regulatory_mapping=regulatory_mapping,
            evidence_freshness=evidence_freshness,
            review_status=review_status,
            reviewer=reviewer,
        )
        gap_types = [gap_type]
        support_status = "supported" if gap_type == "none" else "unsupported"
        unsupported_reason = "" if gap_type == "none" else reason
        downstream_claims = [
            str(mapping.get("claim"))
            for mapping in regulatory_mapping
            if mapping.get("claim")
        ]
        return {
            "claim_support": {
                "claim_id": f"{component_id}:fairness-reviewability",
                "claim_text": (
                    f"Fairness evidence for {component_type} component "
                    "is ready for reviewer assessment."
                ),
                "support_status": support_status,
                "supporting_evidence_refs": evidence_refs,
                "unsupported_reason": unsupported_reason,
            },
            "evidence_gap_type": gap_types,
            "evidence_state_reason": reason,
            "component_fault_localization": {
                "fault_component_id": component_id,
                "upstream_faults": [] if fault == "none" else [fault],
                "downstream_claims_affected": downstream_claims,
                "localization_confidence": "unknown" if gap_type == "none" else "high",
            },
            "reviewer_required_action": action,
        }

    def _component_evidence_gap(
        self,
        *,
        component_type: str,
        evidence: Mapping[str, Any],
        protected_attributes: list[str],
        subgroup_coverage: Mapping[str, Any],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        known_bias_risks: list[Mapping[str, Any]],
        remediations: list[Mapping[str, Any]],
        regulatory_mapping: list[Mapping[str, Any]],
        evidence_freshness: Mapping[str, Any],
        review_status: str,
        reviewer: Any,
    ) -> tuple[str, str, str, str]:
        if not protected_attributes:
            return (
                "missing_protected_attribute_test",
                "No protected attributes are tested for this component.",
                "protected_attributes_tested",
                "request_more_evidence",
            )

        if subgroup_coverage.get("missing_groups"):
            return (
                "missing_subgroup_coverage",
                "Subgroup coverage has missing groups.",
                "subgroup_coverage.missing_groups",
                "request_more_evidence",
            )

        if not subgroup_coverage.get("evaluated_groups"):
            return (
                "missing_subgroup_coverage",
                "No evaluated subgroups are attached.",
                "subgroup_coverage.evaluated_groups",
                "request_more_evidence",
            )

        if evidence_freshness.get("evidence_state") == "stale":
            return (
                "stale_fairness_result",
                "Fairness evidence is stale.",
                "evidence_freshness.evidence_state",
                "request_more_evidence",
            )

        remediation_gap = self._unvalidated_remediation_gap(remediations)
        if remediation_gap is not None:
            return remediation_gap

        if self._has_proxy_risk_without_current_evidence(
            known_bias_risks=known_bias_risks,
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            evidence_freshness=evidence_freshness,
        ):
            return (
                "proxy_risk_not_surfaced",
                "Proxy-related bias risk has no current supporting evidence.",
                "known_bias_risks",
                "request_more_evidence",
            )

        if component_type == "monitor" and not self._has_connected_monitor_evidence(evidence):
            return (
                "disconnected_monitor",
                "Monitor component has no connected live evidence feed.",
                "fairness_evidence.live_feed_connected",
                "request_more_evidence",
            )

        regulatory_gap = self._unsupported_regulatory_gap(regulatory_mapping)
        if regulatory_gap is not None:
            return regulatory_gap

        if review_status.lower() in {"review_required", "pending"} and not reviewer:
            return (
                "missing_reviewer_approval",
                "Review is required or pending but no reviewer is assigned.",
                "review_status",
                "require_human_review",
            )

        return (
            "none",
            "Current reviewer-visible fairness evidence is attached.",
            "none",
            "approve",
        )

    def _unvalidated_remediation_gap(
        self, remediations: list[Mapping[str, Any]]
    ) -> tuple[str, str, str, str] | None:
        for index, remediation in enumerate(remediations):
            status = str(remediation.get("status") or "").lower()
            validation_state = str(remediation.get("validation_state") or "").lower()
            if status in {"attempted", "proposed"} and validation_state in {
                "untested",
                "simulated",
            }:
                return (
                    "unvalidated_remediation",
                    "Remediation is attempted or proposed without validated evidence.",
                    f"remediation_history[{index}].validation_state",
                    "request_more_evidence",
                )
        return None

    def _has_proxy_risk_without_current_evidence(
        self,
        *,
        known_bias_risks: list[Mapping[str, Any]],
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        evidence_freshness: Mapping[str, Any],
    ) -> bool:
        has_proxy_risk = any(
            "proxy" in str(risk.get("risk_id") or "").lower()
            or "proxy" in str(risk.get("description") or "").lower()
            for risk in known_bias_risks
        )
        if not has_proxy_risk:
            return False

        states = self._component_evidence_states(
            fairness_metrics=fairness_metrics,
            bias_tests_run=bias_tests_run,
            known_bias_risks=[],
            regulatory_mapping=[],
            evidence_freshness=evidence_freshness,
        )
        return not any(state in {"current", "reviewed"} for state in states)

    def _has_connected_monitor_evidence(self, evidence: Mapping[str, Any]) -> bool:
        if evidence.get("live_feed_connected") is True:
            return True
        if evidence.get("monitoring_live_feed_connected") is True:
            return True
        if evidence.get("connected_evidence_ref") or evidence.get("live_feed_ref"):
            return True

        live_feed_status = str(evidence.get("live_feed_status") or "").lower()
        monitoring_status = str(evidence.get("monitoring_status") or "").lower()
        connected_states = {"active", "connected", "enabled", "live"}
        return live_feed_status in connected_states or monitoring_status in connected_states

    def _unsupported_regulatory_gap(
        self, regulatory_mapping: list[Mapping[str, Any]]
    ) -> tuple[str, str, str, str] | None:
        unsupported_states = {"missing", "stale", "simulated", "unknown"}
        for index, mapping in enumerate(regulatory_mapping):
            if mapping.get("evidence_state") in unsupported_states:
                return (
                    "unsupported_regulatory_claim",
                    "Regulatory mapping claim is not supported by current evidence.",
                    f"regulatory_mapping[{index}].evidence_state",
                    "request_more_evidence",
                )
        return None

    def _aggregate_risk_summary(self, components: list[Mapping[str, Any]]) -> dict[str, Any]:
        severities = [
            component["risk_summary"]["overall_severity"] for component in components
        ]
        ranked = [
            severity for severity in severities if severity in self._SEVERITY_RANK
        ]
        if ranked:
            overall = max(ranked, key=lambda severity: self._SEVERITY_RANK[severity])
        elif "unknown" in severities:
            overall = "unknown"
        else:
            overall = "low"

        key_risks = []
        for component in components:
            for risk in component["risk_summary"]["key_risks"]:
                if risk not in key_risks:
                    key_risks.append(risk)

        return {
            "overall_severity": overall,
            "key_risks": key_risks,
            "unknown_count": sum(
                component["risk_summary"]["unknown_count"] for component in components
            ),
            "stale_evidence_count": sum(
                component["risk_summary"]["stale_evidence_count"] for component in components
            ),
            "simulated_evidence_count": sum(
                component["risk_summary"]["simulated_evidence_count"]
                for component in components
            ),
            "reviewer_action": self._reviewer_action(
                overall,
                [unknown for component in components for unknown in component["unknowns"]],
            ),
        }

    def _component_evidence_states(
        self,
        *,
        fairness_metrics: list[Mapping[str, Any]],
        bias_tests_run: list[Mapping[str, Any]],
        known_bias_risks: list[Mapping[str, Any]],
        regulatory_mapping: list[Mapping[str, Any]],
        evidence_freshness: Mapping[str, Any],
    ) -> list[str]:
        states = [str(evidence_freshness.get("evidence_state") or "unknown")]
        for collection in (
            fairness_metrics,
            bias_tests_run,
            known_bias_risks,
            regulatory_mapping,
        ):
            states.extend(str(item.get("evidence_state") or "unknown") for item in collection)
        return states

    def _overall_component_severity(
        self,
        known_bias_risks: list[Mapping[str, Any]],
        unknowns: list[str],
    ) -> str:
        ranked = [
            str(risk.get("severity"))
            for risk in known_bias_risks
            if str(risk.get("severity")) in self._SEVERITY_RANK
        ]
        if ranked:
            return max(ranked, key=lambda severity: self._SEVERITY_RANK[severity])
        if unknowns:
            return "unknown"
        return "low"

    def _reviewer_action(self, severity: str, unknowns: list[str]) -> str:
        if severity == "critical":
            return "Reject release approval until required fairness evidence is attached."
        if severity in {"high", "unknown"} or unknowns:
            return "Request missing fairness evidence before release approval."
        if severity == "medium":
            return "Require reviewer sign-off before release approval."
        return "No additional fairness evidence action required."

    def _review_summary(self, review_state: Mapping[str, Any] | None) -> dict[str, Any]:
        review_state = review_state or {}
        return {
            "status": str(review_state.get("status") or "review_required"),
            "reviewer": review_state.get("reviewer"),
            "reviewed_at": review_state.get("reviewed_at"),
            "notes": str(review_state.get("notes") or "Generated by FairMind profile service."),
            "pending_actions": list(review_state.get("pending_actions") or []),
        }

    def _evidence_state(self, state: Any) -> str:
        state = str(state or "unknown").lower()
        if state in self._VALID_EVIDENCE_STATES:
            return state
        return "unknown"

    def _severity(self, severity: Any) -> str:
        severity = str(severity or "unknown").lower()
        if severity in self._VALID_SEVERITIES:
            return severity
        return "unknown"

    def _remediation_validation_state(self, state: Any) -> str:
        state = str(state or "untested").lower()
        if state in {"untested", "simulated", "retrained", "validated", "reviewed"}:
            return state
        return "untested"

    def _get(self, source: Mapping[str, Any] | Any, key: str, *, default: Any) -> Any:
        if isinstance(source, Mapping):
            return source.get(key, default)
        return getattr(source, key, default)

    def _slug(self, value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or "system"

    def _isoformat(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
