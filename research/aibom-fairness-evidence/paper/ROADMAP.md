# AIBOM Fairness Evidence Paper Roadmap

## Strategic Pivot

This paper should not claim to define a new AI Bill of Materials standard. It should study a reviewer-centered evidence profile layered onto existing AI and ML BOM artifacts.

Core thesis:

> AI BOMs make components visible. A fairness evidence profile makes the review status of fairness claims visible across those components.

The paper lives or fails on reviewability: whether reviewers can detect missing, stale, simulated, unsupported, or unreviewed fairness evidence more reliably than they can from a generic AI/ML BOM.

## Phase 0: Claim Reset

Goal: prevent the paper from inheriting broad FairMind platform claims.

Low-level TODOs:

- Use this folder as the canonical paper lane for the AIBOM fairness evidence work.
- Treat `docs/paper/PAPER_DRAFT.md` as background only, not as the manuscript base.
- Keep the title: **Making Bias Evidence Reviewable in AI Bills of Materials**.
- Keep the contribution narrow: reviewability of fairness evidence across BOM components.
- Keep FairMind as the prototype system and artifact generator, not as proof of production-grade fairness assurance.
- Maintain `CLAIM_LEDGER.md` before writing paper claims.

Exit criteria:

- Every major paper claim has an evidence status.
- Unsupported first-of-kind, production-validation, and fairness-proof claims are removed or downgraded.

## Phase 1: Prior-Art Grounding

Goal: make the novelty claim defensible against the strongest adjacent work.

Low-level TODOs:

- Maintain `prior_art_matrix.md`.
- Compare against CycloneDX ML-BOM, CycloneDX modelCard fairness assessment support, Model Cards, Datasheets, Data Cards, NIST AI RMF, NIST AIBOM, OSCAL, AIBoMGen, machine-readable AI compliance evidence, audit-as-code, and continuous AI assurance.
- Explicitly separate existing support for component inventory, model reporting, and machine-readable compliance from this paper's focus on reviewer-visible evidence gaps.
- Avoid strawman baselines.

Exit criteria:

- The paper can answer: "Why is this not just Model Cards plus CycloneDX?"
- The matrix identifies at least one measurable gap this work evaluates.

## Phase 2: Baseline Strengthening

Goal: replace weak generic BOM comparisons with stronger baselines.

Low-level TODOs:

- Keep existing generic ML-BOM examples for simple comparison.
- Add CycloneDX-style comparison examples for loan approval, hiring, and healthcare triage.
- Include realistic component, dependency, model, dataset, and modelCard-like metadata.
- Do not include explicit fairness evidence state, unknown-risk labels, reviewer action, or remediation validation state in the baseline.
- Map each baseline component ID to the fairness profile counterpart.

Exit criteria:

- Reviewers cannot dismiss the evaluation as comparing against an intentionally empty generic BOM.

## Phase 3: Profile Hardening

Goal: sharpen the schema around the paper's actual novelty.

Low-level TODOs:

- Review whether the schema needs explicit fields for claim support, evidence gap type, evidence-state reason, component fault localization, and reviewer-required action.
- Keep "unknown fairness evidence is unknown risk" as an invariant.
- Confirm the generator never upgrades simulated evidence to validated evidence.
- Add tests for unsupported regulatory claims and stale evidence after model updates if missing.

Exit criteria:

- The schema and generator directly support the measured reviewer tasks.

## Phase 4: Reviewer Study Protocol

Goal: turn the existing task cards into a reproducible formative pilot.

Low-level TODOs:

- Create `evaluation/study_protocol.md`.
- Define participants, inclusion criteria, task order, artifacts shown, timing collection, confidence collection, and debrief questions.
- Use a within-subject comparison if feasible: baseline AI/ML BOM versus fairness evidence profile.
- Counterbalance artifact order across reviewers.
- Label any small internal run as formative feedback unless a formal study protocol is used.

Exit criteria:

- A reviewer can run the pilot without asking the authors for hidden instructions.

## Phase 5: Pilot Execution

Goal: collect evidence that the profile improves reviewability.

Minimum pilot:

- Three synthetic systems.
- Twelve reviewer task cards.
- Twenty-four injected faults.
- Three to five reviewers.

Stronger pilot:

- Eight to twelve reviewers.
- Randomized task order.
- Counterbalanced artifact order.
- Explicit timing and confidence capture.

Exit criteria:

- Each task has a decision, localized component, risk label, missing or stale evidence label, confidence score, and rationale.

## Phase 6: Analysis

Goal: analyze reviewability without overstating statistical power.

Low-level TODOs:

- Create `evaluation/analysis_plan.md`.
- Report detection rate, component localization accuracy, false assurance rate, review time, confidence calibration, and unsupported claims accepted.
- For small samples, prefer descriptive statistics and bootstrap confidence intervals over strong significance claims.
- Compare against generic and CycloneDX-style baselines.
- Add qualitative error themes for missed faults.

Exit criteria:

- Results support bounded claims about the pilot or explicitly say the pilot is inconclusive.

## Phase 7: Focused Paper Draft

Goal: write a paper around reviewability, not a broad platform report.

Low-level TODOs:

- Create `draft.md`.
- Suggested structure:
  - Abstract
  - Introduction
  - Motivation: component visibility is not evidence reviewability
  - Related Work
  - Fairness Evidence Profile Design
  - FairMind Prototype
  - Fault-Injection Evaluation
  - Reviewer Pilot
  - Results or Formative Findings
  - Limitations
  - Ethics
  - Conclusion
- Use `CLAIM_LEDGER.md` as a gate before each section is promoted from draft to submission text.

Exit criteria:

- The manuscript does not depend on unsupported FairMind production-readiness claims.

## Phase 8: Submission Package

Goal: prepare a reproducible artifact package.

Low-level TODOs:

- Add an artifact README.
- Preserve schema validation and cross-artifact consistency commands.
- Include examples, baselines, task cards, pilot protocol, analysis plan, and limitation notes.
- Keep synthetic-data ethics explicit.
- Decide venue based on evidence:
  - Poster or workshop if no pilot.
  - Artifact or late-breaking paper if formative pilot exists.
  - Full FAccT, CHI, SOUPS, or AIES paper only after stronger reviewer evidence.

Exit criteria:

- The package can be reviewed independently without relying on live FairMind deployment.

## Immediate Next Target

Implement Phase 0 and Phase 1 first:

1. Claim ledger.
2. Prior-art matrix.
3. Claim scan for overbroad wording.
4. Naming scan to ensure old artifact names do not return.
