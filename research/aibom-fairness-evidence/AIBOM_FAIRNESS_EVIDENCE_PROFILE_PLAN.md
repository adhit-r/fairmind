# AIBOM Fairness Evidence Profile Research Plan

## Working Title

**Making Bias Evidence Reviewable in AI Bills of Materials**

Alternative title:

**A Fairness Evidence Profile for AI Bills of Materials**

## One-Sentence Thesis

Existing AI and ML bills of materials document components and provenance, but they do not make fairness risk, subgroup coverage, remediation status, stale evidence, and reviewer approval visible enough for governance reviewers. This work defines a fairness-evidence profile for AI BOMs so bias risk can be traced across datasets, models, preprocessing, evaluation, remediation, and monitoring.

## Research Goal

Make this idea submission-ready by producing:

- a FairMind integration map,
- a fairness evidence profile schema,
- three realistic fairness evidence profile artifacts,
- a fault-injection evaluation set,
- a small pilot comparison between generic AI/ML BOMs and fairness evidence profiles,
- a SOUPS-ready poster abstract and poster outline.

## Core Research Question

Can a fairness-aware AI BOM help reviewers detect missing, stale, unsupported, or overclaimed fairness evidence across an AI supply chain better than a generic AI/ML BOM?

## Secondary Research Questions

1. Which fairness risks are invisible in generic AI/ML BOMs?
2. What fields are required to make subgroup coverage and bias evidence reviewable?
3. Can an AIBOM fairness evidence profile reduce false assurance when fairness testing is missing, stale, simulated, or not human-reviewed?
4. Can reviewers localize the supply-chain component responsible for a fairness risk faster with an AIBOM fairness evidence profile?

## What Is New

This is not a replacement for CycloneDX ML-BOM, model cards, data cards, or governance reports.

The contribution is a fairness-evidence extension that links:

- component lineage,
- protected attributes tested,
- subgroup coverage,
- fairness metrics,
- bias tests,
- remediation history,
- evidence freshness,
- validation state,
- human review state,
- regulatory mappings.

The key rule:

> Unknown fairness evidence is not low risk. It is unknown risk.

## FairMind Local Evidence

FairMind already has enough surface to support this research direction:

- AI BOM service: `apps/backend/src/application/services/ai_bom_service.py`
- AI BOM database service: `apps/backend/src/application/services/ai_bom_db_service.py`
- bias detection services: `apps/backend/src/application/services/modern_llm_bias_service.py`
- India-specific bias service: `apps/backend/src/application/services/india_bias_detection_service.py`
- benchmark suite generator: `apps/backend/src/application/services/benchmark_suite_service.py`
- automated evidence collector: `apps/backend/src/application/services/automated_evidence_collector.py`
- compliance mapper: `apps/backend/src/application/services/compliance_mapper.py`
- existing paper draft: `docs/paper/PAPER_DRAFT.md`

The research package should use FairMind as the prototype platform. The schema is the fairness evidence profile FairMind can attach to its AI BOM and evidence surfaces; the synthetic examples are FairMind fixtures for schema validation and reviewer-task design, not standalone claims.

Important limitation:

Some existing FairMind paths are synthetic, simulated, default, or in-memory. The paper must not claim production-grade evidence. The profile should explicitly label evidence state instead of hiding this limitation.

## Closest Prior Art

Use these as the baseline positioning:

- CycloneDX ML-BOM: https://cyclonedx.org/capabilities/mlbom/
- NIST SBOM guidance: https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity/software-security-supply-chains/software-1
- NIST AIBOM presentation: https://csrc.nist.gov/Presentations/2024/securing-ai-ecosystems-the-critical-role-of-aibom
- Model Cards for Model Reporting: https://research.google/pubs/pub48120/
- Datasheets for Datasets: https://arxiv.org/abs/1803.09010
- Data Cards: https://research.google/pubs/data-cards-purposeful-and-transparent-dataset-documentation-for-responsible-ai/
- NIST AI RMF: https://www.nist.gov/itl/ai-risk-management-framework
- NIST Generative AI Profile: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf
- EU AI Act: https://artificialintelligenceact.eu/the-act/
- ISO/IEC 42001 overview: https://www.iso.org/standard/42001

Gap statement:

Model cards and data cards document individual artifacts. ML-BOMs document supply-chain components. The fairness evidence profile links fairness evidence, subgroup coverage, remediation status, freshness, and review state across the whole AI supply chain.

## Fairness Evidence Profile Schema Scope

Minimum required fields:

| Field | Purpose |
| --- | --- |
| `component_id` | Stable identifier for the component |
| `component_type` | dataset, model, embedding, preprocessing, evaluation set, remediation, monitor, report |
| `component_name` | Human-readable name |
| `version` | Component version or hash |
| `upstream_components` | Dependencies or source components |
| `downstream_components` | Components affected by this one |
| `protected_attributes_tested` | Attributes included in fairness evaluation |
| `subgroup_coverage` | Group-level representation or missing groups |
| `fairness_metrics` | Demographic parity, equalized odds, disparate impact, etc. |
| `bias_tests_run` | WEAT, SEAT, minimal pairs, FairMind tests, domain tests |
| `known_bias_risks` | Risks and affected groups |
| `remediation_history` | Mitigations attempted and linked evidence |
| `validation_state` | untested, simulated, retrained, validated, reviewed |
| `evidence_refs` | Report IDs, test IDs, hashes, dataset IDs, logs |
| `evidence_freshness` | Timestamp and expiry/staleness rule |
| `review_status` | pending, accepted, rejected, review_required |
| `regulatory_mapping` | NIST AI RMF, ISO 42001, EU AI Act, DPDP, RBI FREE-AI if added |
| `unknowns` | Explicit missing evidence |
| `risk_summary` | Reviewer-facing summary |

## Example Artifacts To Produce

Create this folder structure:

```text
research/aibom-fairness-evidence/
  AIBOM_FAIRNESS_EVIDENCE_PROFILE_PLAN.md
  README.md
  FAIRMIND_INTEGRATION.md
  schema/
    aibom_fairness_evidence.schema.json
  examples/
    loan_approval_fairness_profile.json
    hiring_ranker_fairness_profile.json
    healthcare_triage_fairness_profile.json
    generic_loan_approval_mlbom.json
    generic_hiring_ranker_mlbom.json
    generic_healthcare_triage_mlbom.json
  evaluation/
    fault_injection_cases.csv
    reviewer_task_cards.md
    pilot_results.md
  poster/
    soups_abstract.md
    poster_outline.md
```

## Synthetic Systems

Use three realistic systems:

1. **Loan approval model**
   - risks: proxy discrimination, missing subgroup coverage, stale fairness test, unsupported regulatory claim
   - protected attributes: gender, caste/category proxy, region, language, age

2. **Hiring ranker**
   - risks: biased training labels, education proxy, language proxy, unvalidated remediation
   - protected attributes: gender, age, region, language, disability if synthetic data permits

3. **Healthcare triage model**
   - risks: underrepresented groups, shifted deployment population, missing evaluation set, monitor disconnected
   - protected attributes: gender, age, region, language, socioeconomic proxy

## Fault-Injection Evaluation

Create at least 24 cases across the three systems.

Recommended distribution:

| Fault Type | Cases |
| --- | ---: |
| missing protected attribute test | 3 |
| subgroup missing from evaluation set | 3 |
| stale fairness result after model update | 3 |
| remediation attempted but not validated | 3 |
| proxy feature risk not surfaced | 3 |
| fairness monitor absent or disconnected | 3 |
| unsupported regulatory claim | 3 |
| reviewer approval missing | 3 |

Each case should have:

- `case_id`
- `system`
- `component_id`
- `fault_type`
- `generic_bom_visible`
- `fairness_profile_visible`
- `expected_reviewer_action`
- `severity`
- `ground_truth_explanation`

## Evaluation Conditions

Compare two artifacts:

1. **Generic AI/ML BOM**
   - component list,
   - versions,
   - dependencies,
   - model/dataset metadata,
   - no fairness-specific evidence state.

2. **AIBOM fairness evidence profile**
   - all generic BOM fields,
   - fairness metrics,
   - subgroup coverage,
   - evidence freshness,
   - validation and review state,
   - unknown-risk labels.

## Metrics

Primary metrics:

- evidence gap detection rate,
- root-cause localization accuracy,
- false assurance rate,
- review time,
- reviewer confidence calibration,
- number of unsupported fairness claims accepted.

Secondary metrics:

- audit completeness score,
- missing field count,
- stale evidence detection,
- remediation-overclaim detection,
- regulatory mapping accuracy.

## Pilot Study Plan

Fast version:

- 3 to 5 reviewers,
- 12 task cards,
- compare generic BOM vs AIBOM fairness evidence profile,
- collect accuracy, time, confidence, and qualitative comments.

No human-subjects overclaim:

- If this is informal internal feedback, describe it as formative feedback.
- Do not claim a controlled user study unless formal clearance and protocol exist.
- Use synthetic systems only.
- Do not include real customer, employee, applicant, patient, or protected-class records.

## Reviewer Task Example

Prompt:

> You are reviewing whether this AI system has enough fairness evidence for release approval. Identify any missing, stale, unsupported, or unreviewed fairness claims. Mark the system as approve, reject, or request more evidence.

Expected output:

- decision,
- risk found,
- component responsible,
- evidence missing,
- confidence,
- explanation.

## FairMind Implementation Tasks

### Phase 1: Research Artifact Only

No product code required.

- Create `FAIRMIND_INTEGRATION.md`.
- Create `aibom_fairness_evidence.schema.json`.
- Create three fairness evidence profile examples.
- Create three generic ML-BOM comparison examples.
- Create 24 fault-injection cases.
- Write pilot results template.
- Write SOUPS abstract draft.

### Phase 2: Minimal FairMind Generator

Add a lightweight service:

```text
apps/backend/src/application/services/fairness_evidence_profile_service.py
apps/backend/tests/test_fairness_evidence_profile_service.py
```

Service responsibilities:

- accept or retrieve FairMind AIBOM documents, model metadata, dataset metadata, bias test results, remediation records, human review state, and evidence records;
- produce an AIBOM fairness evidence profile JSON document;
- label missing data as `unknown`, not `low`;
- label simulated results as `simulated`, not `validated`;
- calculate a basic fairness supply-chain risk summary.

Current implementation status:

- `apps/backend/src/application/services/fairness_evidence_profile_service.py` accepts mapping-shaped FairMind records and emits schema-compatible profile JSON.
- `apps/backend/tests/test_fairness_evidence_profile_service.py` covers unknown evidence handling, simulated evidence preservation, review state, and component lineage.

### Phase 3: Optional UI

Add a simple reviewer view later:

- component graph,
- evidence-state badges,
- missing subgroup warnings,
- stale evidence warnings,
- remediation validation status,
- export JSON.

This is optional for the first poster.

## Acceptance Criteria

The research package is ready when:

- schema validates all examples,
- FairMind service-to-profile mapping is written,
- each example has at least 6 components,
- each example includes at least 8 fairness/evidence fields,
- the fault-injection set has at least 24 cases,
- generic BOM vs fairness evidence profile comparison is written,
- every strong claim is supported by a source or marked as a hypothesis,
- no production-grade claims are made about simulated FairMind outputs,
- SOUPS abstract is under 2 pages when formatted.

## Submission Framing

For SOUPS:

**Making Bias Evidence Reviewable in AI Bills of Materials**

SOUPS angle:

- usable security,
- reviewer trust,
- false assurance,
- governance evidence,
- human review of AI supply-chain claims.

Do not frame it as a standards paper only. Frame it as a human-review problem:

> Current AI BOMs can tell reviewers what components exist, but not whether fairness evidence is missing, stale, unvalidated, or overclaimed.

For a journal:

- Journal of Cybersecurity: best interdisciplinary governance fit.
- JISA: good applied security and evidence-system fit.
- Cybersecurity: possible if AI supply-chain security is emphasized.
- TDSC: only if formal dependability or system-security guarantees are added.
- TIFS: weak unless reframed as forensic detection of unsupported fairness claims.

## Five-Day Execution Plan

### Day 1: Scope and Schema

- Freeze title and thesis.
- Create `schema/aibom_fairness_evidence.schema.json`.
- Define validation states and evidence states.
- Write `README.md`.

### Day 2: Examples

- Create loan approval fairness evidence profile.
- Create hiring ranker fairness evidence profile.
- Create healthcare triage fairness evidence profile.
- Create matching generic ML-BOM versions.

### Day 3: Fault Injection

- Create 24 fault cases.
- Map each fault to whether generic BOM or the fairness evidence profile exposes it.
- Write reviewer task cards.

### Day 4: Pilot and Results

- Run internal pilot or simulated reviewer analysis.
- Fill `pilot_results.md`.
- Produce comparison table and key figure.

### Day 5: Submission Material

- Write SOUPS abstract.
- Write poster outline.
- Add ethics statement.
- Add limitations.
- Final QA for claims and citations.

## Strong Claims Allowed

Allowed:

- The AIBOM fairness evidence profile is a proposed evidence layer for AI/ML BOMs.
- The profile makes missing, stale, simulated, and unreviewed fairness evidence explicit.
- FairMind provides the prototype platform for generating and evaluating fairness evidence profile artifacts.
- The initial evaluation uses synthetic systems and fault injection.

Not allowed yet:

- The profile proves fairness.
- The profile replaces model cards, data cards, or CycloneDX ML-BOM.
- FairMind currently provides production-validated fairness evidence profiles.
- Reviewers have been proven to perform better unless an actual reviewed study is run.

## Expected Output Figure

Use one central figure:

```text
Dataset -> Preprocessing -> Model -> Evaluation -> Remediation -> Monitor -> Report
   |            |            |          |             |            |        |
coverage     proxies      version   tests/freshness validation  drift   review
```

Caption:

> The AIBOM fairness evidence profile attaches fairness evidence state to each supply-chain component, making unknown, stale, simulated, and unreviewed fairness claims visible to reviewers.

## Final Readiness Target

Current readiness: **Medium**.

Ready-now target after this plan:

- **SOUPS poster readiness: High** once schema, examples, and fault cases exist.
- **Journal readiness: Medium** until a larger reviewer study or real-world case study is completed.
