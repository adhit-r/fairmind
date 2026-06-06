# Formative Pilot Analysis Plan

This plan defines how to analyze reviewer responses from the AIBOM fairness evidence formative pilot. It is reviewability-centered and does not assume that the fairness evidence profile improves reviewer performance before data is collected.

## Analysis Goals

The analysis asks whether reviewers can detect, localize, and explain fairness evidence gaps across three artifact conditions:

- Generic AI/ML BOM.
- CycloneDX-style ML-BOM with model-card-like metadata.
- AIBOM fairness evidence profile.

The analysis focuses on synthetic task performance and reviewer interpretation. It does not measure production fairness, real-world harm reduction, or deployment readiness.

## Unit Of Analysis

Primary unit:

- One reviewer response to one task under one artifact condition.

Secondary units:

- Reviewer-level summaries across tasks.
- Task-level summaries across reviewers.
- System-level summaries across Loan Approval Model, Hiring Ranker, and Healthcare Triage Model.
- Fault-type summaries using `evaluation/fault_injection_cases.csv`.

## Data Preparation

Before analysis:

- Assign each response a stable reviewer_id that does not reveal identity.
- Verify that each response has task_id, system_id, artifact_condition, elapsed_seconds, decision, confidence, localized_component_id, and rationale_text.
- Join task responses to expected fault cases using task_id, system_id, and artifact condition mapping.
- Code missing values explicitly rather than dropping rows silently.
- Preserve task order and artifact order fields for order-effect review.

Exclude or flag:

- Responses from reviewers who had access to the answer key.
- Author walkthroughs, unless analyzed separately as design feedback.
- Tasks interrupted by tooling failure or facilitator disclosure.
- Duplicate repeated-exposure tasks, unless the protocol intentionally includes repeated exposure.

## Primary Metrics

Detection rate:

- Definition: percentage of injected faults or expected evidence gaps correctly identified by the reviewer.
- Coding: correct, partial, incorrect.
- Report by artifact condition, system, task, and fault type.

Localization accuracy:

- Definition: percentage of detected faults localized to the correct component or evidence object.
- Coding: correct component, related component, incorrect component, no component.
- Report exact and partial localization separately.

False assurance rate:

- Definition: percentage of responses that approve or otherwise accept a release, mitigation, monitoring, or regulatory claim when ground truth indicates missing, stale, unsupported, simulated-only, unreviewed, or unvalidated evidence.
- Count "approve" as false assurance when the expected action is reject or request_more_evidence.
- Count a rationale that accepts an unsupported claim as false assurance even if the final decision is not approve; report this separately as claim-level false assurance.

Review time:

- Definition: elapsed seconds per task and elapsed minutes per artifact block.
- Report median, interquartile range, minimum, and maximum by artifact condition.
- Keep interrupted tasks flagged and report with and without those rows if necessary.

Confidence calibration:

- Definition: relationship between confidence_1_to_5 and correctness.
- Report mean confidence for correct, partial, and incorrect responses.
- Identify high-confidence errors, defined as confidence 4 or 5 with incorrect detection, incorrect localization, or false assurance.

Unsupported claims accepted:

- Definition: count and percentage of unsupported release, regulatory, mitigation, monitoring, or reviewer-approval claims accepted by reviewers.
- Report by artifact condition and unsupported-claim type.
- Include rationale excerpts only in short, anonymized form.

## Secondary Metrics

Decision accuracy:

- Compare reviewer decision to expected action: approve, reject, or request_more_evidence.
- Use strict and lenient coding if needed. For example, reject and request_more_evidence may both be non-approval, but they should remain distinct in the primary table.

Evidence-gap classification accuracy:

- Compare reviewer evidence_gap_type to the injected or expected gap type.
- Categories: missing, stale, simulated_only, unsupported_claim, unreviewed, remediation_unvalidated, proxy_risk, monitor_disconnected, other, none_found.

Rationale support level:

- supported_by_artifact: rationale cites a real field, component, or absence in the artifact.
- unsupported_inference: rationale invents information not present in the artifact.
- unclear: rationale is too vague to evaluate.

## Descriptive Statistics

For small N, prioritize descriptive statistics:

- Counts and percentages for categorical outcomes.
- Median and interquartile range for review time.
- Mean and standard deviation only as supplementary summaries.
- Per-reviewer plots or tables to show heterogeneity rather than hiding it in aggregate rates.
- Per-task tables for hard cases, especially missed faults and high-confidence errors.

Report denominators clearly. For example:

- "4/9 responses detected the stale-evidence fault under the generic condition."
- "2/5 reviewers localized the unsupported release claim to the release report."

## Intervals And Uncertainty

If sample size and tooling allow, compute bootstrap intervals:

- Use reviewer-level resampling when reviewers each complete multiple tasks.
- Use at least 1,000 bootstrap resamples for descriptive intervals.
- Report intervals as exploratory uncertainty bounds, not formal proof.
- Avoid bootstrap intervals for cells with extremely small denominators unless clearly labeled as unstable.

Suggested interval targets:

- Detection rate by artifact condition.
- Localization accuracy by artifact condition.
- False assurance rate by artifact condition.
- Median review time by artifact condition.

## Paired Comparisons

Use paired comparisons only when enough matched data exists.

Minimum requirements:

- The same reviewer completed comparable tasks across the artifact conditions being compared.
- Task exposure order is recorded.
- Repeated exposure to the same fault is either avoided or explicitly modeled as a limitation.
- Each comparison cell has enough observations to make the result interpretable.

Possible paired summaries:

- Within-reviewer difference in detection rate between generic and fairness profile conditions.
- Within-reviewer difference in false assurance rate between CycloneDX-style and fairness profile conditions.
- Within-reviewer difference in median task time across conditions.

For very small N, report paired differences descriptively rather than using significance language. Use terms such as "observed difference in this pilot" instead of "significant improvement."

## Qualitative Error-Theme Coding

Code missed faults, false assurance cases, and confusing rationales into qualitative themes.

Initial codebook:

- Missing evidence not noticed.
- Stale evidence treated as current.
- Simulated-only evidence treated as validated.
- Remediation claim accepted without post-remediation validation.
- Unsupported regulatory or release claim accepted.
- Reviewer approval missing but overlooked.
- Proxy feature risk not recognized.
- Monitor disconnected or incomplete but treated as sufficient.
- Component localization wrong or too broad.
- Baseline artifact lacked enough context.
- Profile field confusing or overstrong.
- Task wording ambiguity.
- Reviewer imported outside assumptions.

Coding process:

- One coder assigns initial codes to each error or notable rationale.
- A second coder reviews a sample or all coded rows when feasible.
- Resolve disagreements by discussion and preserve a short memo explaining code changes.
- Add new codes only when an observed error does not fit the initial codebook.

Report qualitative findings as themes with counts and short paraphrased examples. Do not overgeneralize from a small formative sample.

## Tables To Produce

Core quantitative tables:

- Responses by reviewer, system, task, and artifact condition.
- Detection rate by artifact condition and fault type.
- Localization accuracy by artifact condition and system.
- False assurance rate by artifact condition and claim type.
- Review time by artifact condition.
- Confidence calibration summary.
- Unsupported claims accepted by artifact condition.

Core qualitative tables:

- Missed-fault themes by artifact condition.
- High-confidence error themes.
- Confusing fields or task wording reported in debrief.
- Suggested artifact or protocol revisions.

## Claim Boundaries

Allowed if supported by pilot data:

- "In this formative pilot, reviewers detected N of M injected evidence faults under condition C."
- "The most common missed-fault themes were A, B, and C."
- "Reviewer rationales suggest that field X was confusing in this pilot."
- "Observed false assurance cases occurred when reviewers accepted unsupported claim type Y."

Allowed only with adequate matched data:

- "Within this pilot sample, reviewers had a higher observed detection rate with condition A than condition B."
- "Within this pilot sample, condition A had fewer observed false assurance responses than condition B."

Not allowed from this pilot alone:

- The profile proves fairness.
- The profile guarantees better reviewer performance.
- The profile is production-validated.
- The pilot demonstrates generalizable reviewer performance.
- The artifact is a new standard.
- The profile reduces real-world bias or harm.

## Handling Inconclusive Results

If results are mixed or sparse, report that directly:

- State which metrics were inconclusive and why.
- Identify whether the issue was sample size, task ambiguity, artifact confusion, order effects, or missing data.
- Treat inconclusive results as protocol feedback, not as a failure of the profile.
- Recommend revisions before any larger study.

## Reproducibility Notes

Archive with the analysis:

- The exact artifact files shown to reviewers.
- The task-card version.
- The fault-injection table version.
- The response sheet schema.
- The randomization or counterbalancing schedule.
- Any facilitator clarifications given during sessions.
- Analysis scripts or spreadsheet formulas used to compute metrics.

Every reported number should trace back to a response row, task id, artifact condition, and ground-truth fault mapping.
