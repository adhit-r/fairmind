# FairMind-E Regulatory Crosswalk

This is a research crosswalk, not legal advice or a compliance determination. It maps the FairMind-E ENV controls to governance concepts that can make environmental evidence easier to review.

## FairMind-E ENV Controls

| Control | Purpose | Required evidence |
| --- | --- | --- |
| ENV-1 Boundary and functional unit | Define what the assessment covers and how intensity is normalized. | System boundary, period, workload, functional unit, model or service version, and excluded components. |
| ENV-2 Dual carbon accounting | Record energy and carbon using both location-based and market-based carbon intensity. | `total_kwh`, `total_kg_co2e_location`, `total_kg_co2e_market`, carbon-intensity source, and average or marginal basis. |
| ENV-3 Evidence quality | Keep categorical provenance separate from numeric uncertainty. | `provenance_class`, `uncertainty_pct`, evidence references, vendor cap, and unknown-evidence findings. |
| ENV-4 Gate decision | Convert impact, intensity versus baseline, confidence, and mitigation readiness into a release recommendation. | Risk tier, recommendation, baseline comparison, and reason codes. |
| ENV-5 Mitigation and exception control | Require documented mitigations or time-boxed exceptions when impact or weak evidence blocks release. | Mitigation owner, exception owner, expiry, rationale, reviewer state, and audit trail. |
| ENV-6 Monitoring and reassessment | Keep assessments versioned and refresh them when workload, model, region, supplier, or evidence quality changes. | Append-only assessment versions, review cadence, scenario sweeps, and remediation status. |

## Crosswalk

| FairMind-E control | NIST AI RMF function | ISO/IEC 42001 Annex C and ISO/IEC 42005 fit | EU AI Act Annex XI and Article 95 fit | India Sutra 7 fit | Notes |
| --- | --- | --- | --- | --- | --- |
| ENV-1 Boundary and functional unit | MAP: contextualize the AI system, use case, lifecycle, and affected resources. | ISO/IEC 42005 impact assessment scoping; ISO/IEC 42001 Annex C risk-source identification. | Supports technical documentation by making energy claims traceable to model/system boundaries. | Frames sustainable adoption as a lifecycle governance concern. | Boundary discipline prevents comparing unlike workloads. |
| ENV-2 Dual carbon accounting | MEASURE: define and apply measurement methods. | ISO/IEC 42005 impact identification and analysis; ISO/IEC TR 20226 metric vocabulary. | Annex XI(e) asks for known or estimated model energy consumption; Article 95 supports sustainability KPIs. | Sutra 7 energy-efficiency expectations need measurable energy and carbon evidence. | Location-based and market-based carbon are both required. Scheduling claims must declare average versus marginal CI. |
| ENV-3 Evidence quality | GOVERN and MEASURE: establish measurement governance, traceability, and uncertainty handling. | ISO/IEC 42001 management-system evidence and ISO/IEC 42005 documentation of impact-assessment assumptions. | Helps distinguish known, estimated, vendor-reported, manual, and unknown energy evidence. | Supports accountable, explainable sustainability claims. | Provenance is categorical; uncertainty is numeric. Vendor-reported evidence is capped at 0.60 confidence. |
| ENV-4 Gate decision | MANAGE: prioritize, respond to, and track risks based on assessment outputs. | ISO/IEC 42005 evaluation and response planning; Annex C objectives/risk sources can motivate thresholds. | Can support voluntary Article 95 KPI programs by making environmental objectives operational. | Turns energy-efficiency and frugality into a release-control question. | Weak evidence is itself a finding: moderate impact plus unknown evidence returns `no_go`. |
| ENV-5 Mitigation and exception control | GOVERN and MANAGE: assign accountability and track risk treatment. | ISO/IEC 42001 roles, responsibilities, operational controls, and impact-assessment treatment planning. | Useful for voluntary codes of conduct and documented governance mechanisms. | Aligns with safety, resilience, and sustainability as accountable operating practices. | Exceptions require owner, expiry, and logged rationale; offsets and RECs cannot improve gate outcomes. |
| ENV-6 Monitoring and reassessment | GOVERN, MEASURE, MANAGE: monitor, review, and improve risk controls. | ISO/IEC 42005 monitoring and review; ISO/IEC 42001 continual improvement. | Supports regular KPI reporting under voluntary codes and updated technical documentation when evidence changes. | Sustained energy efficiency requires periodic review, not one-time estimates. | Re-assessment creates a new version rather than mutating prior evidence. |

## Crosswalk Boundaries

- This crosswalk does not certify conformity to NIST, ISO, EU, RBI, or any Indian AI-governance requirement.
- FairMind-E environmental fields should be treated as evidence inputs for governance review, not as legal conclusions.
- When policy text is broader than environmental impact, this document maps only the energy, resource, sustainability, and evidence-governance portions.
