# Poster Outline

## Title

Making Bias Evidence Reviewable in AI Bills of Materials

## Core Message

AIBOMs can show what components exist. Reviewers also need to see whether fairness claims are supported by current, validated, subgroup-specific, and human-reviewed evidence.

## Problem

- Generic AI/ML BOMs expose components, versions, and dependencies.
- Fairness claims often depend on evidence outside the component list.
- Missing, stale, simulated, or unreviewed evidence can create false assurance.
- Reviewers need the evidence state attached to the component responsible for the claim.

## Contribution

- A fairness evidence profile layered onto AI/ML BOM artifacts.
- A FairMind service crosswalk showing how AIBOM, bias detection, evidence collection, monitoring, and compliance mapping feed the profile.
- Three FairMind synthetic profile fixtures: loan approval, hiring ranker, healthcare triage.
- Three generic BOM comparison examples.
- A 24-case fault-injection set for evidence-gap review.
- Reviewer task cards and a formative pilot template.

## Central Figure

```text
Dataset -> Preprocessing -> Model -> Evaluation -> Remediation -> Monitor -> Report
   |            |            |          |             |            |        |
coverage     proxies      version   tests/freshness validation  drift   review
```

Caption: The AIBOM fairness evidence profile attaches fairness evidence state to each supply-chain component, making unknown, stale, simulated, and unreviewed fairness claims visible to reviewers.

## Profile Fields

- Component identity, type, version, upstream and downstream links.
- Protected attributes tested.
- Subgroup coverage and missing groups.
- Fairness metrics and bias tests.
- Known bias risks and affected groups.
- Remediation history and validation state.
- Evidence references and freshness.
- Human review status.
- Regulatory mapping.
- Explicit unknowns.

## Synthetic Systems

| System | Primary Risks |
| --- | --- |
| Loan Approval Model | Proxy discrimination; missing subgroup coverage; stale fairness result; unsupported regulatory claim |
| Hiring Ranker | Biased training labels; education proxy; language proxy; unvalidated remediation |
| Healthcare Triage Model | Underrepresented groups; shifted deployment population; missing evaluation set; disconnected monitor |

## Evaluation Design

Reviewers compare two artifact conditions:

- Generic AI/ML BOM: component inventory, versions, dependencies, model and dataset metadata.
- AIBOM fairness evidence profile: generic component lineage plus fairness metrics, subgroup coverage, evidence freshness, validation state, review state, and explicit unknowns.

Primary metrics:

- Evidence gap detection rate.
- Root-cause localization accuracy.
- False assurance rate.
- Review time.
- Confidence calibration.
- Unsupported fairness claims accepted.

## Expected Takeaway

The profile should make fairness evidence gaps easier to notice and localize than a generic component inventory. This is a hypothesis for formative testing, not a proven result.

## Ethics And Limitations

- Synthetic systems only.
- FairMind fixtures are derived from current service capabilities, not production runtime exports.
- No real customer, applicant, employee, patient, or protected-class records.
- No claim that the profile proves fairness.
- No claim that the profile replaces CycloneDX ML-BOM, model cards, data cards, or governance reports.
- No production-grade FairMind claim.
- No reviewer-performance claim unless a formal study is run.
