# Gating AI Deployment on Environmental Evidence Quality

## Current source of truth

Use `submission.tex` and `submission.pdf` for the CCAI submission. They are
the official-template, double-blind, measured-result version. `paper.tex` and
`paper.pdf` are legacy pre-port artifacts and should not be edited, submitted,
or cited.

The prose snapshot below is retained only as pre-port history; it still has
pre-data language and is superseded by `submission.tex`.

Draft v0.1 for Tackling Climate Change with Machine Learning @ NeurIPS 2026
(Papers track, 4 pages excluding references, non-archival). Port to the
official CCAI template (NeurIPS-based) before submission; deadline 2026-08-29
AoE via OpenReview.

Author: Adhithya Rajasekaran, Axonome (ORCID 0009-0004-1682-7958).
Co-author line TODO: confirm second author (instrument design lead) name,
affiliation, and consent before submission.

---

## Abstract

Carbon-aware governance proposals gate AI deployment on impact magnitude: a
carbon budget, a readiness level, or a risk rating. None of them asks whether
the carbon number itself can be trusted. We present FairMind-E, an
environmental governance module deployed inside an open AI-governance platform,
that makes measurement provenance a first-class release criterion. Each
assessment maps its measurement source to one of five provenance classes, which
cap a numeric evidence-confidence score (vendor-reported figures cap at 0.60;
undisclosed provenance forces 0.0); confidence crossed with an impact tier in a
3x3 decision matrix yields go, conditional_go, or no_go, and the recommendation
blocks the platform's deployment-approval workflow. Offsets and renewable
certificates never improve confidence, tier, or recommendation. On a 14-case
hand-labeled fixture set, the full mechanism reproduces all expected decisions,
while ablated gates that see only carbon magnitude agree with at most half of
them - a consistency check, not a field result, which is why we also present
the design of two studies, instrumented and ready to run with pre-registration planned: a
measurement study in which identical workloads measured three ways (power
tracker, cloud billing, analytic FLOP estimate) receive different confidence
scores and can flip the gate at identical true impact, and a two-arm expert
panel testing whether the matrix changes reviewer coverage and agreement. We
seek workshop feedback on both study designs before data collection completes.

## 1. The gap: a measurement layer with no trust layer

Regulators and standards bodies are building the measurement layer for AI's
environmental footprint: quantification methods inventories (CEN/CLC/TR 18145),
sustainability overviews (ISO/IEC TR 20226), measurement frameworks in
progress (IEEE P7100), and a G7-commissioned inventory that catalogues thirteen
measurement, monitoring, and reporting initiatives. The EU AI Act anticipates
harmonised standards for "reporting and documentation processes to improve AI
systems' resource performance" (Article 40), and GPAI technical documentation
must state known or estimated energy consumption (Annex XI). Yet none of these
instruments - and none of the thirteen catalogued initiatives - defines how the
quality of an environmental claim should condition a deployment decision.

Recent governance research gates on magnitude. Carbon-Aware Governance Gates
embeds carbon budgets in governance layers, with provenance recorded only in
audit logs; G-TRACE gates on sustainability readiness levels, arguing that
"launch blocking without carbon sign-off creates financial-grade controls";
risk-management integrations treat AI carbon as a risk dimension in banking
frameworks. Meanwhile, measurement research has established that reliability
varies sharply with disclosure: metadata-completeness tiers on 5,227 public
models span roughly 1.2x to 2x estimation error, and spend-based fallbacks in
tiered Scope 3 accounting overestimate by 10-40x. The two literatures have not
been connected: a system can sit comfortably under its carbon budget while its
carbon number is untrustworthy, and every published gate would pass it.

FairMind-E connects them. Our claim is narrow and, to our knowledge, unheld:
environmental evidence quality - not only impact magnitude - should gate AI
deployment, operationalized as a provenance-derived confidence score crossed
with an impact tier. The intellectual ancestry is the data-quality tradition in
life-cycle assessment (pedigree matrices and data quality indicators) and the
NUSAP uncertainty pedigree; recent work recommends DQI-style disclosure for
AI-assisted product footprinting but proposes no score, no thresholds, and no
gate. We bring that tradition, inverted, into AI release governance.

## 2. Mechanism

**Provenance classes and confidence.** Every assessment declares its
measurement source, normalized to one of five provenance classes with bounded
confidence ranges: measured (hardware telemetry; 0.85-1.00), tool_estimated
(software power trackers; 0.60-0.85), vendor_reported (cloud provider figures;
0.40-0.60), manual (analytic FLOP estimates; 0.20-0.40), unknown (0.0). A
caller-supplied score is honored but never allowed to exceed its provenance
cap: a claimed 0.95 on vendor-reported data becomes 0.60, and unknown
provenance forces 0.0 regardless of any claimed score. Provenance is
categorical and reported separately from quantified uncertainty (a percent
figure), so a precise-looking number cannot launder a weak source.

**Impact tiers.** Metrics map to low, medium, or high impact per lifecycle
phase (training, fine-tuning, inference, LLM inference), using location-based
carbon for tiering so market instruments cannot lower a gate outcome. The
thresholds are explicitly provisional and are recalibrated from the
measurement study (Section 4); an intensity-versus-baseline ratio can raise a
tier at any confidence but lower it only with measured-grade confidence.

**The decision matrix.** Confidence bands (measured >= 0.70; estimated
0.35-0.69; unknown < 0.35) cross with impact tiers:

| Impact \ Confidence | measured | estimated | unknown |
|---|---|---|---|
| low | go | go | conditional_go |
| medium | conditional_go | conditional_go | no_go |
| high | conditional_go | no_go | no_go |

Confidence 0.0 short-circuits to no_go before matrix lookup: an undisclosed
claim never passes. A conditional_go cannot be approved until it carries a
dated, owned mitigation or an explicit exception (owner, expiry, rationale) -
the exception path makes reviewer overrides auditable instead of informal.
Six controls (ENV-1..ENV-6: boundary, energy accounting, dual location/market
carbon, per-functional-unit efficiency, evidence confidence with disclosed
uncertainty, mitigation/exception) define coverage, and disclosed offsets are
recorded but never subtracted from emissions and never improve any gate output.

## 3. Implementation and consistency evaluation

FairMind-E ships inside FairMind, an open AI-governance platform, not as a
standalone proposal. The decision engine is a framework-agnostic Python package
(57 unit tests covering every matrix cell, band boundary, provenance cap, and
the undisclosed-evidence short-circuit). Assessments persist as versioned
governance evidence; a release gate hooks the platform's existing
deployment-approval workflow and returns HTTP 409 with the blocking reason when
the latest assessment is no_go or an unmitigated conditional_go (15
integration tests). Reviewers get a UI tab with the matrix position, control
coverage, mitigation tracker, and version trail; disclosures export in an
ESRS E1-shaped format. The mechanism is therefore machine-checkable end to
end: given the same assessment payload, the gate decision is deterministic and
reproducible.

**Fixture consistency check.** On 14 hand-labeled cases spanning all matrix
cells, mitigation states, exception paths, and offset disclosures, the full
mechanism reproduces 14/14 expected labels. Ablations degrade sharply: a
carbon-only gate (magnitude thresholds, no evidence dimension) agrees on 7/14;
a generic sustainability score on 6/14; no environmental gate on 3/14;
removing only the exception path or the mitigation-review requirement costs
1-3 cases each. We state the boundary plainly: the authors wrote both the
fixtures and the engine, so this is a consistency and ablation illustration -
evidence that the confidence dimension is load-bearing in the mechanism - and
not an empirical validation. That is what the two studies are for.

## 4. Validation studies (designed and instrumented, pre-data)

**Measurement study (M5).** Four workloads (classical ML training, transformer
fine-tune, RAG inference, batch embeddings) x 5 iterations, each physical run
measured three ways: a software power tracker (tool_estimated), operator-filled
cloud billing (vendor_reported), and a documented analytic FLOP estimate
(manual). The harness never fabricates: missing dependencies or billing entries
yield method_available=false rows. Outputs feed method-agreement statistics
(pairwise MAPE, Bland-Altman limits of agreement) that recalibrate the
provisional tier thresholds and confidence ranges. The design isolates the
paper's central question: the same run, at identical true impact, carries
different provenance under each method - we report how often the gate decision
flips on provenance alone, a quantity no magnitude-only gate can express.

**Expert panel (M6).** Twelve synthetic system profiles cover all nine matrix
cells (boundary cells doubled with differing mitigation states), each validated
against the production engine; 15 raters (5 GRC, 5 ML engineering, 5 ESG) rate
8 profiles each under a counterbalanced assignment (10 ratings per profile,
at least 3 per role). Two arms: baseline (raw measurements only) versus module
(full FairMind-E output). Pre-specified hypotheses: H1, displayed confidence
correlates negatively with recommendation ordinal (Spearman); H2, the module
arm raises ENV control coverage against a per-profile gold checklist (Wilcoxon
signed-rank on paired coverage rates); H3, the matrix improves inter-rater
agreement (mean pairwise Cohen's kappa and Fleiss' kappa with bootstrapped
CIs, target kappa > 0.60). The analysis pipeline is implemented with exact
statistics, environment-independent bootstrap intervals, and hand-verified
test vectors, so results are computable the day collection closes.

## 5. Pathway to impact

The near-term impact channel is regulatory: Article 40's harmonised standards
for resource-performance reporting do not yet exist, and the standards bodies'
current deliverables contain no environmental item. A provenance-scored,
platform-integrated gate is a concrete, testable proposal for what those
standards could require - anticipatory infrastructure rather than commentary.
The mechanism is deployed in an open platform, the fixtures, profiles, harness,
and analysis code are public in the project repository, and both studies are
designed for independent replication. We ask the workshop for critique of the
two study designs - particularly the panel's baseline-arm construction and the
defensibility of provenance caps - while changes are still cheap.

---

## Port status (not part of the paper)

DONE. `submission.tex` is the submission-ready port, built on the official
`tackling_climate_workshop_style.sty` downloaded from climatechange.ai on
2026-07-31. Compile with `tectonic submission.tex`.

Verified against the live call:

- Official style file, loaded with no options, so the style anonymizes the
  author block and adds review line numbers. Never add `final`; add
  `preprint` only for the arXiv posting after the decision.
- Double-blind (confirmed on the 2026 call; the earlier assumption of
  single-blind was wrong). Author renders as "Anonymous Author(s)",
  acknowledgments auto-hide via the `ack` environment, and the system,
  platform, and repository names are withheld behind the `\sysname` and
  `\platname` macros. Verified: zero identifying strings in the source.
- Length: content ends on page 4, references run to page 5 and do not count
  toward the limit.
- Pathway-to-climate-impact statement is its own section, arguing the
  incentive mechanism (evidence quality as a release criterion makes
  measurement effort the cheapest path to approval) and labelling the work a
  leverage point rather than direct abatement.
- Limitations paragraph included.
- Both tables use booktabs with no vertical rules, per the style guidance.

Before submitting:

- Create the OpenReview account. The portal at
  openreview.net/group?id=NeurIPS.cc/2026/Workshop/TCCML opens around
  2026-08-10; account creation itself can take up to two weeks, so do it now.
- Deadline 2026-08-29, 23:59 AoE.
- Confirm the co-author (instrument design lead): name, affiliation, consent.
  The submission is anonymous, so this only has to be settled before the
  camera-ready or preprint, but settle it early.
- Optional if space allows: an ablation bar chart from
  research/fairmind-e/evaluation/plots/paper_baseline_accuracy.svg. The
  ablation currently reads as a table, which is more compact.

For the camera-ready or arXiv preprint: flip `\sysname` to FairMind-E,
`\platname` to FairMind, restore the author block and acknowledgments, add the
repository link, and add the `preprint` style option for arXiv.
