#!/usr/bin/env python3
"""Generate the FairMind-E M6 expert-panel assessment profiles.

Twelve synthetic system assessments cover every cell of the impact x confidence
decision matrix once, plus one extra profile for each conditional_go boundary
cell adjacent to no_go (low+unknown and high+measured) and one extra for
medium+estimated. Each profile reads like a real system submission so that
human raters can judge it without seeing the engine's answer.

Outputs (deterministic, stdlib-only):
    profiles/profiles.json     machine-readable profiles with expected labels
    profiles/PROFILES.md       printable panel pack, no answer key
    profiles/ANSWER_KEY.md     expected labels, coverage, and rationales
    panel/assignment_plan.csv  counterbalanced rater x profile assignment

``--validate`` replays every profile through the production domain engine
(``apps/backend/src/domain/environmental``) and fails on any label mismatch.
Generation itself needs only the standard library; validation needs the
backend environment (pydantic), matching ``evaluation/evaluate_gate.py``.
"""

from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
from typing import Any


PACKAGE_ROOT = pathlib.Path(__file__).resolve().parents[1]

# 9 matrix cells once each, plus the two conditional_go boundary cells adjacent
# to no_go (low+unknown, high+measured) and medium+estimated a second time.
MATRIX_CELL_TARGETS: dict[str, int] = {
    "low+measured": 1,
    "low+estimated": 1,
    "low+unknown": 2,
    "medium+measured": 1,
    "medium+estimated": 2,
    "medium+unknown": 1,
    "high+measured": 2,
    "high+estimated": 1,
    "high+unknown": 1,
}

RATER_ROLES = ("GRC", "ML_ENG", "ESG")
RATERS_PER_ROLE = 5
PROFILES_PER_RATER = 8
EXCLUSION_BLOCK = 4

ASSIGNMENT_COLUMNS = ["rater_id", "role", "position", "profile_id"]

CONTROL_CODES = ["ENV-1", "ENV-2", "ENV-3", "ENV-4", "ENV-5", "ENV-6"]

METRIC_LABELS: list[tuple[str, str]] = [
    ("total_kwh", "Total energy (kWh)"),
    ("total_kg_co2e_location", "Location-based carbon (kgCO2e)"),
    ("total_kg_co2e_market", "Market-based carbon (kgCO2e)"),
    ("kg_co2e_per_1000_requests", "Efficiency (kgCO2e per 1000 requests)"),
    ("kg_co2e_per_1m_tokens", "Efficiency (kgCO2e per 1M tokens)"),
    ("location_carbon_intensity_g_co2e_per_kwh", "Location grid intensity (gCO2e/kWh)"),
    ("market_carbon_intensity_g_co2e_per_kwh", "Market grid intensity (gCO2e/kWh)"),
    ("carbon_intensity_basis", "Carbon intensity basis"),
    ("pue", "Power usage effectiveness (PUE)"),
    ("energy_renewable_pct", "Renewable energy share (percent)"),
]


PROFILES: list[dict[str, Any]] = [
    {
        "id": "P01",
        "title": "KisanScore agri-credit risk model retraining",
        "matrix_cell": "low+measured",
        "domain": "agri_credit_scoring",
        "market": "india",
        "description": [
            "KisanScore v3 is the crop-season credit risk model of a Pune-based "
            "non-banking financial company that lends to smallholder farmers across "
            "Maharashtra and Madhya Pradesh. The model is a gradient-boosted tree "
            "ensemble trained on 38 million historical repayment records, mandi price "
            "feeds, and district-level rainfall data, and it prices roughly 400,000 "
            "loan applications each season.",
            "The quarterly retraining run executes on the company's own eight-node CPU "
            "cluster in its Pune data centre. Rack-level PDU meters and per-socket RAPL "
            "counters were logged for the full run, and western regional grid emission "
            "factors were applied to the metered kilowatt-hours. Market-based figures "
            "reflect the renewable energy certificates the lender retires against its "
            "data-centre load.",
            "The submission covers the complete hyperparameter search and final fit for "
            "the 2026 kharif-season model. Feature-store serving, training-data storage, "
            "and the loan officers' scoring interface sit outside the declared boundary.",
        ],
        "assessment": {
            "system_id": "kisanscore-agri-credit-v3",
            "lifecycle_phase": "training",
            "functional_unit": "training_run",
            "period_start": "2026-04-07",
            "period_end": "2026-04-11",
            "boundary_json": {
                "description": "Quarterly retraining of the KisanScore v3 gradient-boosted ensemble, including the hyperparameter search and final fit, on the lender's Pune CPU cluster.",
                "includes": ["hyperparameter search", "final model fit", "cooling overhead via PUE"],
                "excludes": ["feature-store serving", "training-data storage", "loan-officer scoring interface"],
            },
            "metrics": {
                "total_kwh": 54.0,
                "total_kg_co2e_location": 38.3,
                "total_kg_co2e_market": 34.6,
                "location_carbon_intensity_g_co2e_per_kwh": 710.0,
                "market_carbon_intensity_g_co2e_per_kwh": 640.0,
                "carbon_intensity_basis": "average",
                "pue": 1.6,
            },
            "provenance_class": "measured",
            "measurement_source": "rack PDU meters and per-socket RAPL counters",
            "confidence_score": 0.92,
            "uncertainty_pct": 6.0,
            "intensity_vs_baseline": 0.94,
            "evidence_refs_json": [
                "pdu-export-2026q2.csv",
                "rapl-log-kisanscore-v3.parquet",
                "western-grid-factors-2026.pdf",
            ],
        },
        "expected": {
            "provenance_class": "measured",
            "confidence_score": 0.92,
            "confidence_band": "measured",
            "risk_tier": "low",
            "recommendation": "go",
            "approval_blocking": False,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "missing",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "Metered PDU and RAPL evidence yields a 0.92 confidence score in the "
            "measured band, and 38.3 kgCO2e for a classical training run sits well "
            "inside the low tier. The (low, measured) cell resolves to go with nothing "
            "to block approval. ENV-4 is missing only because a per-request efficiency "
            "figure does not apply to a training-run functional unit."
        ),
        "mitigation_design": "Go cell: no mitigation required; approval is not blocking.",
    },
    {
        "id": "P02",
        "title": "LexRetrieve statute and case-law RAG search",
        "matrix_cell": "low+estimated",
        "domain": "rag_search",
        "market": "international",
        "description": [
            "LexRetrieve is the retrieval service behind a Dublin-based legal research "
            "product used by law firms in Ireland and the Netherlands. Each query embeds "
            "the user question with a compact bi-encoder, retrieves candidate passages "
            "from a statute and case-law index, and returns re-ranked citations. Roughly "
            "twelve million queries were served in the June 2026 window.",
            "Engineering instrumented the retrieval pods with CodeCarbon, which sampled "
            "node power and applied Irish grid intensity for the location figure and the "
            "provider's green-tariff residual mix for the market figure. Tool estimates "
            "were cross-checked against pod CPU-seconds; the residual uncertainty is "
            "dominated by shared-node attribution.",
            "The declared boundary covers embedding, index search, and re-ranking for "
            "production queries. The nightly index rebuild is assessed separately and is "
            "excluded here.",
        ],
        "assessment": {
            "system_id": "lexretrieve-rag-search",
            "lifecycle_phase": "inference",
            "functional_unit": "1000_requests",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Production query path of the LexRetrieve service: query embedding, index search, and re-ranking for the June 2026 window (about 12 million queries).",
                "includes": ["query embedding", "index search", "re-ranking"],
                "excludes": ["nightly index rebuild", "document ingestion pipeline"],
            },
            "metrics": {
                "total_kwh": 16.5,
                "total_kg_co2e_location": 4.8,
                "total_kg_co2e_market": 2.0,
                "kg_co2e_per_1000_requests": 0.0004,
                "location_carbon_intensity_g_co2e_per_kwh": 290.0,
                "market_carbon_intensity_g_co2e_per_kwh": 120.0,
                "carbon_intensity_basis": "average",
                "pue": 1.2,
            },
            "provenance_class": "tool_estimated",
            "measurement_source": "CodeCarbon 2.5 on the retrieval pods",
            "confidence_score": 0.66,
            "uncertainty_pct": 22.0,
            "intensity_vs_baseline": 0.88,
            "evidence_refs_json": [
                "codecarbon-emissions-2026-06.csv",
                "green-tariff-residual-mix-2026.pdf",
            ],
        },
        "expected": {
            "provenance_class": "tool_estimated",
            "confidence_score": 0.66,
            "confidence_band": "estimated",
            "risk_tier": "low",
            "recommendation": "go",
            "approval_blocking": False,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 1.0,
        },
        "rationale": (
            "CodeCarbon tool estimation supports a 0.66 score in the estimated band, "
            "and 0.0004 kgCO2e per 1000 requests is comfortably low impact. The "
            "(low, estimated) cell resolves to go, and the profile carries full "
            "ENV-1..6 coverage."
        ),
        "mitigation_design": "Go cell: no mitigation required; approval is not blocking.",
    },
    {
        "id": "P03",
        "title": "TalentSift resume screening ranker",
        "matrix_cell": "low+unknown",
        "domain": "hiring",
        "market": "international",
        "description": [
            "TalentSift ranks incoming resumes for enterprise recruiting teams at a "
            "Denver-based HR software vendor. A distilled transformer scores each resume "
            "against the job requisition; about eight million screening requests were "
            "processed in the June 2026 window across two US production regions.",
            "No energy instrumentation exists yet. A platform engineer produced a "
            "spreadsheet estimate from model FLOPs, an assumed accelerator utilisation "
            "of 40 percent, and a national average grid factor. The team did not compute "
            "a market-based figure, and although instrumentation options are being "
            "discussed, no owner or target date has been attached to any of them.",
        ],
        "assessment": {
            "system_id": "talentsift-resume-ranker",
            "lifecycle_phase": "inference",
            "functional_unit": "1000_requests",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Resume scoring API across the two US production regions for the June 2026 window (about 8 million screening requests).",
                "includes": ["resume scoring API"],
                "excludes": ["model retraining", "recruiter web application"],
                "assumptions": "National average grid factor; accelerator utilisation assumed at 40 percent.",
            },
            "metrics": {
                "total_kwh": 12.6,
                "total_kg_co2e_location": 4.8,
                "kg_co2e_per_1000_requests": 0.0006,
                "location_carbon_intensity_g_co2e_per_kwh": 380.0,
                "carbon_intensity_basis": "average",
            },
            "provenance_class": "manual",
            "measurement_source": "engineering FLOP worksheet",
            "confidence_score": 0.30,
            "uncertainty_pct": 45.0,
            "intensity_vs_baseline": 1.05,
            "mitigation_readiness": "missing",
            "evidence_refs_json": ["flop-estimate-worksheet-v2.xlsx"],
        },
        "expected": {
            "provenance_class": "manual",
            "confidence_score": 0.30,
            "confidence_band": "unknown",
            "risk_tier": "low",
            "recommendation": "conditional_go",
            "approval_blocking": True,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "missing",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "missing",
            },
            "coverage_rate": 0.6667,
        },
        "rationale": (
            "A manual FLOP worksheet caps evidence at 0.30, inside the unknown band, "
            "while impact stays low, so the (low, unknown) cell returns conditional_go. "
            "With no dated mitigation and no exception the release is approval-blocking. "
            "The missing market-based figure also leaves ENV-3 uncovered."
        ),
        "mitigation_design": (
            "Conditional_go deliberately left without a dated mitigation or exception: "
            "approval_blocking is true (contrast with P10)."
        ),
    },
    {
        "id": "P04",
        "title": "TriageAssist clinical intake fine-tune",
        "matrix_cell": "medium+measured",
        "domain": "healthcare_triage",
        "market": "india",
        "description": [
            "TriageAssist is a clinical intake assistant for a hospital network that "
            "operates 14 facilities across Telangana and Andhra Pradesh. The network "
            "fine-tuned an open 8-billion-parameter model on de-identified triage notes "
            "and nurse-line transcripts so the assistant can suggest acuity levels and "
            "department routing in English and Telugu.",
            "The two-week fine-tune ran on a metered eight-GPU cluster in the network's "
            "Hyderabad facility. Rack PDU energy logs supplied kilowatt-hours, southern "
            "regional grid factors supplied the location figure, and market figures net "
            "off the facility's partial renewable certificates. The AI platform team has "
            "signed a dated plan to move the next fine-tuning cycle to the Bengaluru "
            "colocation covered by a solar power purchase agreement.",
        ],
        "assessment": {
            "system_id": "triageassist-clinical-finetune",
            "lifecycle_phase": "fine_tune",
            "functional_unit": "fine_tune_run",
            "period_start": "2026-05-04",
            "period_end": "2026-05-18",
            "boundary_json": {
                "description": "Supervised fine-tune of an open 8B model on de-identified triage notes on the Hyderabad eight-GPU cluster, including evaluation passes.",
                "includes": ["fine-tuning epochs", "evaluation passes"],
                "excludes": ["base-model pretraining", "inference serving", "annotation tooling"],
            },
            "metrics": {
                "total_kwh": 1875.0,
                "total_kg_co2e_location": 1350.0,
                "total_kg_co2e_market": 1143.8,
                "location_carbon_intensity_g_co2e_per_kwh": 720.0,
                "market_carbon_intensity_g_co2e_per_kwh": 610.0,
                "carbon_intensity_basis": "average",
                "pue": 1.5,
            },
            "provenance_class": "measured",
            "measurement_source": "rack PDU energy logs",
            "confidence_score": 0.90,
            "uncertainty_pct": 8.0,
            "intensity_vs_baseline": 1.10,
            "mitigations_json": [
                {
                    "description": "Move the next fine-tuning cycle to the Bengaluru colocation covered by the solar power purchase agreement and re-run this assessment on metered evidence.",
                    "owner": "Head of Clinical AI Platform",
                    "target_date": "2026-10-15",
                    "expected_reduction_pct": 35.0,
                    "status": "proposed",
                }
            ],
            "evidence_refs_json": [
                "pdu-energy-log-2026-05.csv",
                "southern-grid-factors-2026.pdf",
                "solar-ppa-migration-plan.pdf",
            ],
        },
        "expected": {
            "provenance_class": "measured",
            "confidence_score": 0.90,
            "confidence_band": "measured",
            "risk_tier": "medium",
            "recommendation": "conditional_go",
            "approval_blocking": False,
            "has_dated_mitigation": True,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "missing",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "Metered fine-tune evidence scores 0.90 in the measured band and 1350 "
            "kgCO2e sits mid-range in the medium tier, so the (medium, measured) cell "
            "returns conditional_go. The dated solar-PPA migration plan documents "
            "mitigation, so the conditional release is not approval-blocking."
        ),
        "mitigation_design": "Dated mitigation documented: approval_blocking is false.",
    },
    {
        "id": "P05",
        "title": "UPI fraud scoring service",
        "matrix_cell": "medium+estimated",
        "domain": "fraud_detection",
        "market": "india",
        "description": [
            "A Mumbai payments company scores UPI transactions for fraud in real time "
            "with a gradient-boosted ensemble backed by a graph feature service. The "
            "June 2026 window covered about 45 million scoring requests across two cloud "
            "regions during peak festival-season traffic.",
            "Environmental figures come from the cloud provider's sustainability "
            "dashboard, which reports location-based and market-based carbon for the "
            "tagged workloads but does not expose the underlying kilowatt-hours, and its "
            "methodology is not independently auditable. The platform team claims high "
            "confidence in the numbers, but the evidence class remains vendor-reported.",
            "A dated migration of the scoring fleet to the provider's hydro-backed "
            "region, with the metered energy export API enabled, is committed for "
            "November and is already in progress.",
        ],
        "assessment": {
            "system_id": "upi-fraud-scoring-service",
            "lifecycle_phase": "inference",
            "functional_unit": "1000_requests",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Real-time UPI fraud scoring across two production cloud regions for the June 2026 window (about 45 million requests), as tagged in the provider sustainability dashboard.",
                "includes": ["scoring API", "graph feature service"],
                "excludes": ["model training", "case-review tooling", "data warehouse"],
            },
            "metrics": {
                "total_kg_co2e_location": 171.0,
                "total_kg_co2e_market": 149.0,
                "kg_co2e_per_1000_requests": 0.0038,
                "carbon_intensity_basis": "average",
            },
            "provenance_class": "vendor_reported",
            "measurement_source": "cloud provider sustainability dashboard",
            "confidence_score": 0.88,
            "uncertainty_pct": 30.0,
            "intensity_vs_baseline": 1.02,
            "mitigations_json": [
                {
                    "description": "Migrate the scoring fleet to the provider's hydro-backed region and enable the metered energy export API for direct kilowatt-hour evidence.",
                    "owner": "FinCrime Platform Lead",
                    "target_date": "2026-11-30",
                    "expected_reduction_pct": 40.0,
                    "status": "in_progress",
                }
            ],
            "evidence_refs_json": [
                "provider-sustainability-dashboard-2026-06.pdf",
                "hydro-region-migration-ticket.pdf",
            ],
        },
        "expected": {
            "provenance_class": "vendor_reported",
            "confidence_score": 0.60,
            "confidence_band": "estimated",
            "risk_tier": "medium",
            "recommendation": "conditional_go",
            "approval_blocking": False,
            "has_dated_mitigation": True,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "missing",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "The claimed 0.88 confidence is capped at 0.60 because vendor-reported "
            "dashboard evidence can never exceed the vendor cap, landing in the "
            "estimated band, while 0.0038 kgCO2e per 1000 requests is medium impact. "
            "The (medium, estimated) cell returns conditional_go and the dated "
            "hydro-region migration keeps it from blocking approval. The undisclosed "
            "kilowatt-hours leave ENV-2 uncovered."
        ),
        "mitigation_design": "Dated mitigation documented: approval_blocking is false (contrast with P12).",
    },
    {
        "id": "P06",
        "title": "Workspace chat assistant serving",
        "matrix_cell": "medium+unknown",
        "domain": "llm_chat",
        "market": "international",
        "description": [
            "A productivity software company embeds a conversational assistant in its "
            "flagship product for drafting, summarising, and answering workspace "
            "questions. The assistant serves a 70-billion-parameter model behind a "
            "token-streaming API; June 2026 traffic was about 2.1 billion generated "
            "tokens across three serving regions.",
            "The sustainability lead assembled the June estimate manually from "
            "published per-token energy figures for comparable 70B-class deployments, "
            "an assumed PUE of 1.3, and a blended grid factor across the three regions. "
            "There is no telemetry from the serving fleet, and billing data cannot be "
            "decomposed to the assistant workload. The team acknowledges the figure "
            "could move materially in either direction.",
        ],
        "assessment": {
            "system_id": "workspace-chat-assistant",
            "lifecycle_phase": "llm_inference",
            "functional_unit": "1m_tokens",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Token generation for the embedded workspace assistant across three serving regions in June 2026 (about 2.1 billion generated tokens).",
                "includes": ["token generation"],
                "excludes": ["model training", "search indexing", "client applications"],
                "assumptions": "Per-token energy from published figures for comparable 70B-class deployments; PUE assumed at 1.3; blended grid factor across regions.",
            },
            "metrics": {
                "total_kwh": 23000.0,
                "total_kg_co2e_location": 9660.0,
                "total_kg_co2e_market": 8740.0,
                "kg_co2e_per_1m_tokens": 4.6,
                "location_carbon_intensity_g_co2e_per_kwh": 420.0,
                "market_carbon_intensity_g_co2e_per_kwh": 380.0,
                "carbon_intensity_basis": "average",
                "pue": 1.3,
            },
            "provenance_class": "manual",
            "measurement_source": "sustainability-team estimate from published per-token figures",
            "confidence_score": 0.28,
            "uncertainty_pct": 40.0,
            "intensity_vs_baseline": 1.18,
            "evidence_refs_json": ["assistant-footprint-estimate-2026-06.xlsx"],
        },
        "expected": {
            "provenance_class": "manual",
            "confidence_score": 0.28,
            "confidence_band": "unknown",
            "risk_tier": "medium",
            "recommendation": "no_go",
            "approval_blocking": True,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 1.0,
        },
        "rationale": (
            "The manual estimate scores 0.28, in the unknown band, while 4.6 kgCO2e "
            "per million tokens is medium impact, so the (medium, unknown) cell returns "
            "no_go. Full ENV-1..6 coverage cannot rescue evidence that is too weak for "
            "a medium-impact release, and a no_go always blocks approval."
        ),
        "mitigation_design": "No_go cell: approval_blocking is true regardless of mitigation.",
    },
    {
        "id": "P07",
        "title": "Biomedical domain LLM pretraining run",
        "matrix_cell": "high+measured",
        "domain": "domain_llm_pretraining",
        "market": "international",
        "description": [
            "A US biomedical research laboratory pretrained a 13-billion-parameter "
            "domain language model on curated literature, clinical guidelines, and "
            "licensed textbook corpora to support downstream extraction and "
            "evidence-synthesis tools. The run processed roughly 500 billion tokens "
            "over six weeks on the laboratory's HPC partition.",
            "Node-level IPMI power telemetry and facility PUE were logged for the full "
            "run. Hourly average regional grid intensity supplied the location figure, "
            "and the laboratory's wind power purchase agreement is reflected in the "
            "market figure. Operations has signed a dated plan to place the next "
            "pretraining cycle in the overnight low-carbon window using the "
            "carbon-aware scheduler and to publish per-checkpoint energy budgets.",
        ],
        "assessment": {
            "system_id": "biomed-domain-llm-pretrain",
            "lifecycle_phase": "training",
            "functional_unit": "training_run",
            "period_start": "2026-04-01",
            "period_end": "2026-05-15",
            "boundary_json": {
                "description": "Full pretraining run of the 13B biomedical language model on the laboratory HPC partition, including checkpoint evaluation jobs.",
                "includes": ["pretraining", "checkpoint evaluation jobs"],
                "excludes": ["corpus licensing and preprocessing", "downstream fine-tunes"],
            },
            "metrics": {
                "total_kwh": 152000.0,
                "total_kg_co2e_location": 62320.0,
                "total_kg_co2e_market": 33440.0,
                "location_carbon_intensity_g_co2e_per_kwh": 410.0,
                "market_carbon_intensity_g_co2e_per_kwh": 220.0,
                "carbon_intensity_basis": "average",
                "pue": 1.15,
                "energy_renewable_pct": 45.0,
            },
            "provenance_class": "measured",
            "measurement_source": "node IPMI power telemetry",
            "confidence_score": 0.95,
            "uncertainty_pct": 5.0,
            "intensity_vs_baseline": 1.12,
            "mitigations_json": [
                {
                    "description": "Schedule the next pretraining cycle in the overnight low-carbon window using the carbon-aware scheduler and publish per-checkpoint energy budgets.",
                    "owner": "HPC Operations Director",
                    "target_date": "2026-09-30",
                    "expected_reduction_pct": 25.0,
                    "status": "proposed",
                }
            ],
            "evidence_refs_json": [
                "ipmi-telemetry-2026q2.parquet",
                "hourly-grid-intensity-2026q2.csv",
                "wind-ppa-contract-summary.pdf",
            ],
        },
        "expected": {
            "provenance_class": "measured",
            "confidence_score": 0.95,
            "confidence_band": "measured",
            "risk_tier": "high",
            "recommendation": "conditional_go",
            "approval_blocking": False,
            "has_dated_mitigation": True,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "missing",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "IPMI-metered training evidence scores 0.95 in the measured band and "
            "62,320 kgCO2e is high impact, so the (high, measured) cell returns "
            "conditional_go. The dated scheduling and energy-budget plan documents "
            "mitigation, so approval is not blocked."
        ),
        "mitigation_design": (
            "Dated mitigation documented: approval_blocking is false "
            "(contrast with the P11 exception path in the same cell)."
        ),
    },
    {
        "id": "P08",
        "title": "Indic multilingual LLM continued pretraining",
        "matrix_cell": "high+estimated",
        "domain": "multilingual_llm_training",
        "market": "india",
        "description": [
            "A Bengaluru startup ran continued pretraining of a 7-billion-parameter "
            "multilingual model across ten Indic languages, positioning it for "
            "government-service chat and voice interfaces. The five-week run used a "
            "rented GPU cluster located in a coal-heavy grid region.",
            "Energy was not metered. The team reconstructed consumption with a "
            "green-algorithms style calculator from scheduler GPU-hours, card TDP, and "
            "an assumed 65 percent utilisation profile, then applied national grid "
            "factors. The startup discloses retired verified carbon units covering "
            "roughly the estimated footprint and treats that purchase as its primary "
            "environmental answer. Mitigation for the next run is described as planned, "
            "but no owner or target date has been documented.",
        ],
        "assessment": {
            "system_id": "indic-multilingual-llm-cpt",
            "lifecycle_phase": "training",
            "functional_unit": "training_run",
            "period_start": "2026-05-01",
            "period_end": "2026-06-05",
            "boundary_json": {
                "description": "Continued pretraining of the 7B multilingual model across ten Indic languages on a rented GPU cluster.",
                "includes": ["continued pretraining"],
                "excludes": ["base checkpoint training", "instruction tuning", "serving"],
                "assumptions": "GPU-hours and TDP reconstructed from scheduler logs; utilisation assumed at 65 percent.",
            },
            "metrics": {
                "total_kwh": 40600.0,
                "total_kg_co2e_location": 28623.0,
                "total_kg_co2e_market": 28420.0,
                "location_carbon_intensity_g_co2e_per_kwh": 705.0,
                "market_carbon_intensity_g_co2e_per_kwh": 700.0,
                "carbon_intensity_basis": "average",
            },
            "provenance_class": "tool_estimated",
            "measurement_source": "green-algorithms style calculator over scheduler logs",
            "confidence_score": 0.64,
            "uncertainty_pct": 24.0,
            "intensity_vs_baseline": 1.20,
            "mitigation_readiness": "planned",
            "offsets_json": {"retired_kg_co2e": 30000.0},
            "evidence_refs_json": [
                "scheduler-gpu-hours-2026-05.csv",
                "calculator-worksheet-cpt.pdf",
                "vcu-retirement-certificate.pdf",
            ],
        },
        "expected": {
            "provenance_class": "tool_estimated",
            "confidence_score": 0.64,
            "confidence_band": "estimated",
            "risk_tier": "high",
            "recommendation": "no_go",
            "approval_blocking": True,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "missing",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "The tool-reconstructed estimate scores 0.64 in the estimated band and "
            "28,623 kgCO2e is high impact, so the (high, estimated) cell returns "
            "no_go. Retired carbon units are disclosed but never improve confidence, "
            "tier, or the gate, and the absence of a dated mitigation is moot for a "
            "no_go, which always blocks approval."
        ),
        "mitigation_design": "No_go cell: approval_blocking is true; disclosed offsets deliberately do not rescue the gate.",
    },
    {
        "id": "P09",
        "title": "Third-party document-intelligence API",
        "matrix_cell": "high+unknown",
        "domain": "document_intelligence",
        "market": "international",
        "description": [
            "An enterprise contracts team routes scanned agreements through a "
            "third-party document-intelligence API that performs OCR and generates "
            "structured summaries with a large generative model. About 600 million "
            "generated tokens were consumed in June 2026, and the vendor operates the "
            "model as a managed black box across undisclosed regions.",
            "The vendor declined to disclose energy, carbon, hardware, or region "
            "information, citing commercial confidentiality, and publishes no "
            "sustainability documentation for the service. The efficiency figure on "
            "file is the team's own worst-case screening replication using an open "
            "model of assumed similar size on previous-generation accelerators; the "
            "vendor has neither confirmed nor corrected it. No uncertainty "
            "quantification accompanies the submission because there is no disclosure "
            "to quantify.",
        ],
        "assessment": {
            "system_id": "thirdparty-document-intelligence",
            "lifecycle_phase": "llm_inference",
            "functional_unit": "1m_tokens",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Contract OCR and structured summarisation through the managed third-party API for the June 2026 window (about 600 million generated tokens).",
                "includes": ["vendor-hosted OCR and summarisation"],
                "excludes": ["in-house retrieval and review tooling"],
                "assumptions": "Efficiency figure is the team's worst-case screening replication with an open model of assumed similar size; the vendor has not confirmed it.",
            },
            "metrics": {
                "kg_co2e_per_1m_tokens": 18.0,
            },
            "source": "undisclosed",
            "notes": "Vendor declined energy, carbon, hardware, and region disclosure citing commercial confidentiality.",
        },
        "expected": {
            "provenance_class": "unknown",
            "confidence_score": 0.0,
            "confidence_band": "unknown",
            "risk_tier": "high",
            "recommendation": "no_go",
            "approval_blocking": True,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "missing",
                "ENV-3": "missing",
                "ENV-4": "present",
                "ENV-5": "missing",
                "ENV-6": "present",
            },
            "coverage_rate": 0.5,
        },
        "rationale": (
            "The vendor discloses nothing, so provenance is unknown and confidence is "
            "forced to 0.0, which returns no_go before any matrix lookup. The "
            "worst-case screening figure of 18 kgCO2e per million generated tokens "
            "tiers the workload high, but the undisclosed evidence drives the label. "
            "Coverage exists only for the boundary, the efficiency figure, and the "
            "vacuously satisfied mitigation control."
        ),
        "mitigation_design": "No_go cell: approval_blocking is true; undisclosed provenance forces confidence 0.0.",
    },
    {
        "id": "P10",
        "title": "Digital lending pre-qualification scorer",
        "matrix_cell": "low+unknown",
        "domain": "lending",
        "market": "india",
        "description": [
            "A digital lending non-banking financial company pre-qualifies "
            "personal-loan applicants with a logistic scorecard refined by a small "
            "gradient-boosted model. The Chennai region deployment scored about six "
            "million applications in June 2026.",
            "The platform team estimated energy from container CPU allocation and the "
            "southern grid factor in a documented worksheet; no measurement tooling is "
            "deployed yet. Unlike earlier submissions from the same team, this one "
            "carries a dated instrumentation commitment: CodeCarbon on the scoring "
            "containers, with a re-submission on tool-estimated evidence by "
            "mid-September.",
        ],
        "assessment": {
            "system_id": "lending-prequal-scorer",
            "lifecycle_phase": "inference",
            "functional_unit": "1000_requests",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Personal-loan pre-qualification scoring in the Chennai region for the June 2026 window (about 6 million applications).",
                "includes": ["scoring containers"],
                "excludes": ["bureau data ingestion", "collections analytics"],
                "assumptions": "Energy estimated from container CPU allocation and the southern grid factor.",
            },
            "metrics": {
                "total_kwh": 4.2,
                "total_kg_co2e_location": 3.0,
                "total_kg_co2e_market": 3.0,
                "kg_co2e_per_1000_requests": 0.0005,
                "location_carbon_intensity_g_co2e_per_kwh": 710.0,
                "market_carbon_intensity_g_co2e_per_kwh": 710.0,
                "carbon_intensity_basis": "average",
            },
            "provenance_class": "manual",
            "measurement_source": "container CPU allocation worksheet",
            "confidence_score": 0.32,
            "uncertainty_pct": 42.0,
            "intensity_vs_baseline": 0.96,
            "mitigations_json": [
                {
                    "description": "Deploy CodeCarbon instrumentation on the scoring containers and re-submit this assessment on tool-estimated evidence.",
                    "owner": "Credit Platform Engineering Manager",
                    "target_date": "2026-09-15",
                    "status": "in_progress",
                }
            ],
            "evidence_refs_json": [
                "cpu-allocation-worksheet-2026-06.xlsx",
                "instrumentation-rollout-plan.pdf",
            ],
        },
        "expected": {
            "provenance_class": "manual",
            "confidence_score": 0.32,
            "confidence_band": "unknown",
            "risk_tier": "low",
            "recommendation": "conditional_go",
            "approval_blocking": False,
            "has_dated_mitigation": True,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 1.0,
        },
        "rationale": (
            "A documented manual worksheet scores 0.32, in the unknown band, with low "
            "impact, so the (low, unknown) cell returns conditional_go. Unlike P03, "
            "the dated CodeCarbon instrumentation commitment documents mitigation, so "
            "the conditional release is not approval-blocking."
        ),
        "mitigation_design": "Dated evidence-improvement mitigation documented: approval_blocking is false (contrast with P03).",
    },
    {
        "id": "P11",
        "title": "Marketplace search re-ranking LLM serving",
        "matrix_cell": "high+measured",
        "domain": "ecommerce_ranking",
        "market": "international",
        "description": [
            "A global marketplace re-ranks search results with a large language model "
            "that scores the candidate set for every query. The Singapore and Frankfurt "
            "fleets consumed about 2.4 billion scored tokens in June 2026, and "
            "relevance gains from the ranker directly drive gross merchandise volume.",
            "The serving fleet is fully metered: smart-PDU telemetry is aggregated per "
            "model endpoint, and location and market figures are computed from hourly "
            "grid data. Per-token carbon is high because every query fans out to score "
            "dozens of candidates on previous-generation accelerators.",
            "Rather than a dated efficiency mitigation, the VP of Platform Engineering "
            "signed a formal exception recording the contracted fourth-quarter "
            "migration to next-generation hardware, with quarterly review until the "
            "exception expires at year end.",
        ],
        "assessment": {
            "system_id": "marketplace-reranker-llm",
            "lifecycle_phase": "llm_inference",
            "functional_unit": "1m_tokens",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "LLM re-ranking of search candidate sets on the Singapore and Frankfurt fleets for the June 2026 window (about 2.4 billion scored tokens).",
                "includes": ["candidate-set scoring"],
                "excludes": ["first-stage retrieval", "catalogue indexing", "model training"],
            },
            "metrics": {
                "total_kwh": 66900.0,
                "total_kg_co2e_location": 34788.0,
                "total_kg_co2e_market": 32112.0,
                "kg_co2e_per_1m_tokens": 14.5,
                "location_carbon_intensity_g_co2e_per_kwh": 520.0,
                "market_carbon_intensity_g_co2e_per_kwh": 480.0,
                "carbon_intensity_basis": "average",
                "energy_renewable_pct": 20.0,
            },
            "provenance_class": "measured",
            "measurement_source": "smart-PDU telemetry per model endpoint",
            "confidence_score": 0.88,
            "uncertainty_pct": 7.0,
            "intensity_vs_baseline": 1.22,
            "exception": {
                "owner": "VP Platform Engineering",
                "expiry": "2026-12-31",
                "rationale": "Accelerator fleet migration to next-generation hardware is contracted for Q4 2026; interim operation approved with quarterly review.",
            },
            "evidence_refs_json": [
                "smart-pdu-endpoint-telemetry-2026-06.parquet",
                "hourly-grid-data-sg-fra.csv",
                "exception-record-vp-platform.pdf",
            ],
        },
        "expected": {
            "provenance_class": "measured",
            "confidence_score": 0.88,
            "confidence_band": "measured",
            "risk_tier": "high",
            "recommendation": "conditional_go",
            "approval_blocking": False,
            "has_dated_mitigation": False,
            "has_exception": True,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "present",
            },
            "coverage_rate": 1.0,
        },
        "rationale": (
            "Fully metered serving evidence scores 0.88 in the measured band and 14.5 "
            "kgCO2e per million tokens is high impact, so the (high, measured) cell "
            "returns conditional_go. There is no dated mitigation, but the signed "
            "exception with owner, expiry, and rationale satisfies the gate, so "
            "approval is not blocked."
        ),
        "mitigation_design": (
            "Owned exception instead of a dated mitigation: approval_blocking is false "
            "via the exception path (contrast with P07)."
        ),
    },
    {
        "id": "P12",
        "title": "Enterprise semantic embedding pipeline",
        "matrix_cell": "medium+estimated",
        "domain": "embedding_pipeline",
        "market": "international",
        "description": [
            "A Toronto analytics vendor maintains semantic search over customer "
            "document stores. A nightly pipeline embeds new and changed content with a "
            "350-million-parameter encoder, processing about 38 million embedding "
            "requests in June 2026 across two regions, many of them long multi-page "
            "documents.",
            "Instrumentation attached to the inference gateway estimates per-request "
            "energy and carbon with documented assumptions, in the style of EcoLogits. "
            "Off-peak batching and a distilled encoder are both under discussion as "
            "reduction options, but neither has an owner or a target date, and no "
            "exception has been requested from the review board.",
        ],
        "assessment": {
            "system_id": "semantic-embedding-pipeline",
            "lifecycle_phase": "inference",
            "functional_unit": "1000_requests",
            "period_start": "2026-06-01",
            "period_end": "2026-06-30",
            "boundary_json": {
                "description": "Nightly and incremental embedding of customer document stores with the 350M encoder across two regions for the June 2026 window (about 38 million embedding requests).",
                "includes": ["embedding requests", "gateway preprocessing"],
                "excludes": ["vector-store serving", "retrieval API", "encoder training"],
            },
            "metrics": {
                "total_kwh": 338.0,
                "total_kg_co2e_location": 152.1,
                "total_kg_co2e_market": 135.2,
                "kg_co2e_per_1000_requests": 0.004,
                "location_carbon_intensity_g_co2e_per_kwh": 450.0,
                "market_carbon_intensity_g_co2e_per_kwh": 400.0,
                "carbon_intensity_basis": "average",
                "pue": 1.25,
            },
            "provenance_class": "tool_estimated",
            "measurement_source": "EcoLogits-style gateway instrumentation",
            "confidence_score": 0.62,
            "uncertainty_pct": 20.0,
            "intensity_vs_baseline": 1.08,
            "mitigation_readiness": "planned",
            "evidence_refs_json": [
                "gateway-instrumentation-export-2026-06.csv",
                "estimation-assumptions-note.pdf",
            ],
        },
        "expected": {
            "provenance_class": "tool_estimated",
            "confidence_score": 0.62,
            "confidence_band": "estimated",
            "risk_tier": "medium",
            "recommendation": "conditional_go",
            "approval_blocking": True,
            "has_dated_mitigation": False,
            "has_exception": False,
            "coverage": {
                "ENV-1": "present",
                "ENV-2": "present",
                "ENV-3": "present",
                "ENV-4": "present",
                "ENV-5": "present",
                "ENV-6": "missing",
            },
            "coverage_rate": 0.8333,
        },
        "rationale": (
            "Gateway tool estimation scores 0.62 in the estimated band and 0.004 "
            "kgCO2e per 1000 requests is medium impact, so the (medium, estimated) "
            "cell returns conditional_go. The batching and distillation ideas carry no "
            "owner or date and no exception was requested, so the release is "
            "approval-blocking, unlike P05."
        ),
        "mitigation_design": (
            "Conditional_go with undated intentions only: approval_blocking is true "
            "(contrast with P05)."
        ),
    },
]


def matrix_cell_counts(profiles: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for profile in profiles:
        cell = profile["matrix_cell"]
        counts[cell] = counts.get(cell, 0) + 1
    return counts


def check_design(profiles: list[dict[str, Any]]) -> None:
    """Assert the structural invariants of the profile set and panel design."""
    if len(profiles) != 12:
        raise AssertionError(f"expected 12 profiles, found {len(profiles)}")
    ids = [profile["id"] for profile in profiles]
    if ids != [f"P{index:02d}" for index in range(1, 13)]:
        raise AssertionError(f"profile ids must be P01..P12 in order, found {ids}")
    counts = matrix_cell_counts(profiles)
    if counts != MATRIX_CELL_TARGETS:
        raise AssertionError(f"matrix cell coverage mismatch: {counts} != {MATRIX_CELL_TARGETS}")

    rows = assignment_rows(profiles)
    if len(rows) != len(RATER_ROLES) * RATERS_PER_ROLE * PROFILES_PER_RATER:
        raise AssertionError(f"expected 120 assignment rows, found {len(rows)}")
    per_profile: dict[str, int] = {}
    per_profile_role: dict[tuple[str, str], int] = {}
    for row in rows:
        per_profile[row["profile_id"]] = per_profile.get(row["profile_id"], 0) + 1
        key = (row["profile_id"], row["role"])
        per_profile_role[key] = per_profile_role.get(key, 0) + 1
    if set(per_profile.values()) != {10}:
        raise AssertionError(f"every profile must receive exactly 10 ratings: {per_profile}")
    if min(per_profile_role.values()) < 2:
        raise AssertionError(f"every profile needs >= 2 raters per role: {per_profile_role}")


def assignment_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Deterministic counterbalanced rater x profile assignment.

    Fifteen raters (five per role) each rate eight of the twelve profiles.
    Rater ``i`` (0-indexed) skips the cyclic block of four profiles starting at
    ``4 * i mod 12`` and rates the complementary cyclic run of eight, rotated by
    ``i mod 8`` to vary presentation order. The exclusion blocks distribute so
    that every profile receives exactly ten ratings, with three or four raters
    from each role. No randomness is used.
    """
    profile_ids = [profile["id"] for profile in profiles]
    rows: list[dict[str, Any]] = []
    for index in range(len(RATER_ROLES) * RATERS_PER_ROLE):
        rater_id = f"R{index + 1:02d}"
        role = RATER_ROLES[index // RATERS_PER_ROLE]
        start = (EXCLUSION_BLOCK * index + EXCLUSION_BLOCK) % len(profile_ids)
        order = [(start + offset) % len(profile_ids) for offset in range(PROFILES_PER_RATER)]
        rotation = index % PROFILES_PER_RATER
        order = order[rotation:] + order[:rotation]
        for position, profile_index in enumerate(order, start=1):
            rows.append(
                {
                    "rater_id": rater_id,
                    "role": role,
                    "position": position,
                    "profile_id": profile_ids[profile_index],
                }
            )
    return rows


def fmt_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def render_metrics_table(metrics: dict[str, Any]) -> str:
    lines = ["| Metric | Value |", "| --- | ---: |"]
    for key, label in METRIC_LABELS:
        if metrics.get(key) is None:
            continue
        lines.append(f"| {label} | {fmt_value(metrics[key])} |")
    return "\n".join(lines)


def render_boundary(boundary: dict[str, Any]) -> list[str]:
    lines = [f"- Boundary: {boundary['description']}"]
    if boundary.get("includes"):
        lines.append(f"  - Includes: {'; '.join(boundary['includes'])}")
    if boundary.get("excludes"):
        lines.append(f"  - Excludes: {'; '.join(boundary['excludes'])}")
    if boundary.get("assumptions"):
        lines.append(f"  - Assumptions: {boundary['assumptions']}")
    return lines


def render_submission(assessment: dict[str, Any]) -> str:
    """Render one assessment as the rater-facing submission block."""
    lines: list[str] = []
    lines.append(f"- System id: `{assessment['system_id']}`")
    lines.append(f"- Lifecycle phase: {assessment['lifecycle_phase']}")
    lines.append(f"- Functional unit: {assessment['functional_unit']}")
    lines.append(
        f"- Assessment period: {assessment['period_start']} to {assessment['period_end']}"
    )
    lines.extend(render_boundary(assessment["boundary_json"]))

    provenance = assessment.get("provenance_class") or assessment.get("source")
    source = assessment.get("measurement_source")
    if source:
        lines.append(f"- Declared evidence provenance: {provenance} ({source})")
    else:
        lines.append(f"- Declared evidence provenance: {provenance}")
    claimed = assessment.get("confidence_score")
    lines.append(
        "- Self-reported confidence score: "
        + (fmt_value(claimed) if claimed is not None else "not provided")
    )
    uncertainty = assessment.get("uncertainty_pct")
    lines.append(
        "- Reported uncertainty: "
        + (f"{fmt_value(uncertainty)} percent" if uncertainty is not None else "not provided")
    )
    baseline = assessment.get("intensity_vs_baseline")
    lines.append(
        "- Intensity vs approved baseline: "
        + (fmt_value(baseline) if baseline is not None else "not provided")
    )
    if assessment.get("mitigation_readiness"):
        lines.append(f"- Declared mitigation readiness: {assessment['mitigation_readiness']}")

    lines.append("")
    lines.append(render_metrics_table(assessment["metrics"]))
    lines.append("")

    mitigations = assessment.get("mitigations_json") or []
    if mitigations:
        lines.append("- Documented mitigations:")
        for mitigation in mitigations:
            parts = [mitigation["description"]]
            if mitigation.get("owner"):
                parts.append(f"owner: {mitigation['owner']}")
            if mitigation.get("target_date"):
                parts.append(f"target date: {mitigation['target_date']}")
            if mitigation.get("expected_reduction_pct") is not None:
                parts.append(
                    f"expected reduction: {fmt_value(mitigation['expected_reduction_pct'])} percent"
                )
            if mitigation.get("status"):
                parts.append(f"status: {mitigation['status']}")
            lines.append(f"  - {' | '.join(parts)}")
    else:
        lines.append("- Documented mitigations: none declared")

    exception = assessment.get("exception")
    if exception:
        lines.append(
            "- Exception on file: owner: "
            f"{exception['owner']} | expiry: {exception['expiry']} | rationale: {exception['rationale']}"
        )
    else:
        lines.append("- Exception on file: none")

    offsets = assessment.get("offsets_json") or {}
    if offsets:
        disclosed = "; ".join(f"{key}: {fmt_value(value)}" for key, value in offsets.items())
        lines.append(f"- Disclosed offsets or credits: {disclosed}")
    else:
        lines.append("- Disclosed offsets or credits: none")

    refs = assessment.get("evidence_refs_json") or []
    if refs:
        lines.append(f"- Evidence references: {', '.join(f'`{ref}`' for ref in refs)}")
    if assessment.get("notes"):
        lines.append(f"- Notes: {assessment['notes']}")
    return "\n".join(lines)


def render_panel_pack(profiles: list[dict[str, Any]]) -> str:
    """Rater-facing pack: descriptions and submissions, no expected labels."""
    parts: list[str] = []
    parts.append(
        """# FairMind-E Expert-Panel Profile Pack (M6)

Twelve synthetic AI-system environmental assessments for independent expert
rating. Every profile is fictional; names, figures, and documents do not refer
to real organisations. Do not discuss profiles with other raters until your
ratings are submitted.

## Rating task

For each profile assigned to you on the panel schedule, record on the response
form:

1. Release recommendation: `go`, `conditional_go`, or `no_go`.
2. Impact risk tier: `low`, `medium`, or `high`.
3. Evidence confidence band: `measured`, `estimated`, or `unknown`.
4. Approval blocking: `yes` if you would withhold deployment approval in the
   submission's current state, otherwise `no`.
5. A short free-text rationale (one to three sentences).

Judge each submission exactly as presented: the declared boundary, metrics,
evidence provenance, mitigations, exceptions, and disclosures are everything
the review board would see."""
    )
    for profile in profiles:
        parts.append(f"\n---\n\n## {profile['id']}: {profile['title']}\n")
        parts.append("\n\n".join(profile["description"]))
        parts.append("\n### Assessment submission\n")
        parts.append(render_submission(profile["assessment"]))
    return "\n".join(parts) + "\n"


def render_answer_key(profiles: list[dict[str, Any]]) -> str:
    """Panel-analysis answer key: expected labels, coverage, and rationales."""
    parts: list[str] = []
    parts.append(
        """# FairMind-E Expert-Panel Answer Key (M6)

Expected engine labels for the twelve panel profiles. Keep this file separate
from `PROFILES.md`; raters must not see it before submitting ratings. Every
label below is validated against the production domain engine
(`apps/backend/src/domain/environmental`) by `generate_profiles.py --validate`
and `tests/test_profiles.py`.

## Overview

| ID | Matrix cell | Provenance | Confidence | Band | Tier | Recommendation | Blocking |
| --- | --- | --- | ---: | --- | --- | --- | --- |"""
    )
    for profile in profiles:
        expected = profile["expected"]
        parts.append(
            "| {id} | {cell} | {prov} | {score} | {band} | {tier} | {rec} | {blocking} |".format(
                id=profile["id"],
                cell=profile["matrix_cell"],
                prov=expected["provenance_class"],
                score=f"{expected['confidence_score']:.2f}",
                band=expected["confidence_band"],
                tier=expected["risk_tier"],
                rec=expected["recommendation"],
                blocking=fmt_value(expected["approval_blocking"]),
            )
        )
    parts.append(
        """
Matrix coverage: all nine impact x confidence cells appear once; the
conditional_go boundary cells adjacent to no_go (low+unknown via P03/P10 and
high+measured via P07/P11) and medium+estimated (P05/P12) each appear twice.
Within each doubled cell the two profiles deliberately differ in mitigation or
exception state so that approval blocking varies while the recommendation does
not."""
    )
    for profile in profiles:
        expected = profile["expected"]
        parts.append(f"\n## {profile['id']}: {profile['title']}\n")
        parts.append(f"- Matrix cell: {profile['matrix_cell']}")
        parts.append(f"- Expected recommendation: {expected['recommendation']}")
        parts.append(f"- Expected risk tier: {expected['risk_tier']}")
        parts.append(
            f"- Expected confidence: {expected['confidence_score']:.2f} "
            f"({expected['confidence_band']} band, provenance {expected['provenance_class']})"
        )
        parts.append(f"- Expected approval blocking: {fmt_value(expected['approval_blocking'])}")
        parts.append(f"- Dated mitigation: {fmt_value(expected['has_dated_mitigation'])}")
        parts.append(f"- Owned exception: {fmt_value(expected['has_exception'])}")
        coverage = " | ".join(
            f"{code} {expected['coverage'][code]}" for code in CONTROL_CODES
        )
        parts.append(f"- Control coverage: {coverage}")
        parts.append(f"- Coverage rate: {expected['coverage_rate']:g}")
        parts.append(f"- Mitigation design: {profile['mitigation_design']}")
        parts.append(f"\n{profile['rationale']}")
    return "\n".join(parts) + "\n"


def build_profiles_document(profiles: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "title": "FairMind-E M6 expert-panel assessment profiles",
        "generated_by": "research/fairmind-e/profiles/generate_profiles.py",
        "profile_count": len(profiles),
        "matrix_cells": matrix_cell_counts(profiles),
        "profiles": profiles,
    }


def write_text(path: pathlib.Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_assignment_csv(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=ASSIGNMENT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def load_engine() -> tuple[Any, Any]:
    """Import the production domain engine, mirroring evaluate_gate.py."""
    repo_root = pathlib.Path(__file__).resolve().parents[3]
    backend_root = repo_root / "apps" / "backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from src.domain.environmental import EnvironmentalAssessment, run_assessment

    return EnvironmentalAssessment, run_assessment


def validate_profiles(profiles: list[dict[str, Any]]) -> list[str]:
    """Replay every profile through the production engine; return mismatches."""
    environmental_assessment, run_assessment = load_engine()
    failures: list[str] = []
    for profile in profiles:
        expected = profile["expected"]
        payload = environmental_assessment(**profile["assessment"]).normalized_payload()
        result = run_assessment(payload)

        checks: list[tuple[str, Any, Any]] = [
            ("provenance_class", expected["provenance_class"], result.provenance_class),
            ("confidence_band", expected["confidence_band"], result.confidence_band),
            ("risk_tier", expected["risk_tier"], result.risk_tier),
            ("recommendation", expected["recommendation"], result.recommendation),
            ("approval_blocking", expected["approval_blocking"], bool(result.approval_blocking)),
            (
                "has_dated_mitigation",
                expected["has_dated_mitigation"],
                bool(result.has_dated_mitigation),
            ),
            ("has_exception", expected["has_exception"], bool(result.has_exception)),
            ("coverage", expected["coverage"], dict(result.coverage)),
        ]
        for name, expected_value, actual_value in checks:
            if expected_value != actual_value:
                failures.append(
                    f"{profile['id']}: {name} expected {expected_value!r}, engine returned {actual_value!r}"
                )
        if abs(expected["confidence_score"] - float(result.confidence_score)) > 1e-6:
            failures.append(
                f"{profile['id']}: confidence_score expected {expected['confidence_score']}, "
                f"engine returned {result.confidence_score}"
            )
        if abs(expected["coverage_rate"] - float(result.coverage_rate)) > 1e-6:
            failures.append(
                f"{profile['id']}: coverage_rate expected {expected['coverage_rate']}, "
                f"engine returned {result.coverage_rate}"
            )
    return failures


def generate(output_root: pathlib.Path) -> dict[str, pathlib.Path]:
    check_design(PROFILES)
    paths = {
        "profiles_json": output_root / "profiles" / "profiles.json",
        "panel_pack": output_root / "profiles" / "PROFILES.md",
        "answer_key": output_root / "profiles" / "ANSWER_KEY.md",
        "assignment_plan": output_root / "panel" / "assignment_plan.csv",
    }
    write_text(
        paths["profiles_json"],
        json.dumps(build_profiles_document(PROFILES), indent=2) + "\n",
    )
    write_text(paths["panel_pack"], render_panel_pack(PROFILES))
    write_text(paths["answer_key"], render_answer_key(PROFILES))
    write_assignment_csv(paths["assignment_plan"], assignment_rows(PROFILES))
    return paths


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=pathlib.Path,
        default=PACKAGE_ROOT,
        help="research/fairmind-e root to write profiles/ and panel/ outputs under",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="replay every profile through the production engine before writing",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    check_design(PROFILES)

    if args.validate:
        failures = validate_profiles(PROFILES)
        if failures:
            for failure in failures:
                print(f"MISMATCH {failure}")
            print(f"validation failed: {len(failures)} mismatches across {len(PROFILES)} profiles")
            return 1
        print(f"validation passed: {len(PROFILES)}/{len(PROFILES)} profiles match the engine")

    paths = generate(args.output_root)
    for name, path in paths.items():
        print(f"wrote {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
