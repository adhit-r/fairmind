# Formative Pilot Study Protocol

This protocol is for formative review of synthetic FairMind fixtures. It is designed to test whether the AIBOM fairness evidence profile makes fairness evidence gaps reviewable when compared with baseline AI/ML BOM artifacts. It does not establish production assurance, fairness certification, or a controlled-study result unless a separate formal human-subjects protocol and approval process are completed.

## Purpose

The pilot evaluates reviewer workflows for identifying missing, stale, simulated, unsupported, or unreviewed fairness evidence across AI system components.

Primary purpose:

- Assess whether reviewers can find and explain fairness evidence gaps from three artifact conditions.
- Identify fields, labels, or task wording that confuse reviewers before any larger study.
- Produce bounded formative evidence for refining the fairness evidence profile and task materials.

## Research Questions

RQ1: Can reviewers detect injected fairness evidence faults from each artifact condition?

RQ2: Can reviewers localize each detected fault to the responsible component or evidence object?

RQ3: Do reviewers accept unsupported release, regulatory, or mitigation claims at different rates across artifact conditions?

RQ4: How do review time, confidence, and rationale quality vary across artifact conditions?

RQ5: Which profile fields or baseline omissions explain missed faults, false assurance, or reviewer confusion?

## Participants

Target pilot size:

- Minimum formative run: 3 to 5 reviewers.
- Stronger formative run: 8 to 12 reviewers.

Inclusion criteria:

- Familiarity with at least one of AI governance, software supply chain review, model risk review, ML evaluation, fairness assessment, compliance review, security review, or technical audit.
- Ability to read JSON-like evidence artifacts and complete structured task forms in English.
- No role in authoring the exact task card answers, fault injection table, or ground-truth labels for the materials they review.

Exclusion criteria:

- Prior access to the ground-truth answer key for the same pilot round.
- Direct authorship of the specific profile examples or baseline examples being reviewed, unless the session is explicitly labeled an author walkthrough rather than reviewer pilot data.

## Synthetic Systems

The pilot uses three synthetic systems:

- Loan Approval Model.
- Hiring Ranker.
- Healthcare Triage Model.

All systems are synthetic fixtures. They are not production deployments and should not be described as evidence about real people, real organizations, or live model behavior.

## Artifact Conditions

Each reviewer compares three artifact conditions:

1. Generic AI/ML BOM.
2. CycloneDX-style ML-BOM with model-card-like metadata.
3. AIBOM fairness evidence profile.

Condition definitions:

- Generic AI/ML BOM: component inventory and high-level model or dataset details without explicit fairness evidence state, reviewer action, or remediation validation state.
- CycloneDX-style ML-BOM: stronger baseline with component, dependency, model, dataset, and model-card-like metadata, but without the profile-specific evidence-state and unknown-risk framing.
- AIBOM fairness evidence profile: profile artifact that makes fairness evidence state, evidence gaps, component localization, remediation validation state, reviewer action, and unsupported claim risk explicit.

The pilot should use matched systems across conditions. For each synthetic system, the baseline artifacts and fairness profile should refer to corresponding components whenever possible.

## Materials

Required materials:

- `evaluation/reviewer_task_cards.md`.
- `evaluation/fault_injection_cases.csv`.
- Generic baseline examples in `examples/generic_*_mlbom.json`.
- CycloneDX-style baseline examples in `examples/cyclonedx_style_*_mlbom.json`.
- Fairness profile examples in `examples/*_fairness_profile.json`.
- Response capture sheet or form using the fields listed in this protocol.

Do not provide reviewers with `evaluation/fault_injection_cases.csv` or expected-focus notes during task execution. Those files are for facilitator setup and analysis.

## Task Flow

1. Consent and orientation, 5 minutes.
   - Explain that the materials are synthetic.
   - Explain that the task evaluates artifact reviewability, not reviewer competence.
   - Explain that reviewers should not infer production readiness beyond the artifacts shown.

2. Practice task, 5 to 8 minutes.
   - Use a small synthetic example not included in the main task set.
   - Verify that the reviewer understands the decision labels and confidence scale.

3. Main task blocks, 45 to 75 minutes.
   - Reviewers complete task cards for the three systems.
   - Each task presents one system and one artifact condition.
   - Reviewers record decision, component localization, evidence gap, confidence, timing, and rationale.

4. Debrief, 10 to 15 minutes.
   - Ask which artifacts made review easier or harder and why.
   - Ask which fields were confusing, missing, or too strong.
   - Ask whether any artifact wording implied stronger assurance than the evidence supported.

## Counterbalancing

Use a within-subject design when feasible: each reviewer sees all three artifact conditions, but no reviewer should see the same task/system in all conditions back-to-back.

Recommended counterbalancing:

- Rotate artifact condition order across reviewers using a Latin-square-style sequence:
  - Reviewer group A: Generic, CycloneDX-style, Fairness Profile.
  - Reviewer group B: CycloneDX-style, Fairness Profile, Generic.
  - Reviewer group C: Fairness Profile, Generic, CycloneDX-style.
- Rotate system order across reviewers:
  - Loan Approval Model, Hiring Ranker, Healthcare Triage Model.
  - Hiring Ranker, Healthcare Triage Model, Loan Approval Model.
  - Healthcare Triage Model, Loan Approval Model, Hiring Ranker.
- Avoid showing a reviewer the same fault case twice in different conditions unless the session explicitly studies repeated-exposure effects.

If sample size is too small for complete counterbalancing, record the exact order shown and treat order effects as a limitation.

## Timing

Collect timing at two levels:

- Per task: start timestamp, end timestamp, elapsed seconds.
- Per artifact block: start timestamp, end timestamp, elapsed minutes.

Pause the timer for facilitator interruptions, tool failures, or consent/debrief discussion. Record any paused intervals in notes.

## Confidence Collection

After each task, collect reviewer confidence on a 1 to 5 scale:

- 1: Guessing.
- 2: Low confidence.
- 3: Moderate confidence.
- 4: High confidence.
- 5: Very high confidence.

Confidence should be collected before the reviewer receives feedback or sees another condition for a similar task.

## Rationale Capture

For each task, collect a short free-text rationale. Ask reviewers to cite the artifact field, component, or absence of evidence that drove the decision.

Suggested prompt:

"Briefly explain the evidence or missing evidence that led to your decision. Name the component or field if possible."

Do not correct the reviewer during the task unless they ask for procedural clarification. Clarifications should not reveal expected faults.

## Response Data Fields

Collect one row per reviewer-task-condition response.

Required fields:

- pilot_id.
- reviewer_id.
- reviewer_background_category.
- prior_fairness_review_experience: none, limited, moderate, extensive.
- prior_bom_or_supply_chain_review_experience: none, limited, moderate, extensive.
- system_id.
- system_name.
- task_id.
- artifact_condition: generic_mlbom, cyclonedx_style_mlbom, fairness_evidence_profile.
- artifact_file.
- artifact_order_index.
- system_order_index.
- task_start_time.
- task_end_time.
- elapsed_seconds.
- decision: approve, reject, request_more_evidence.
- risk_found: free text or coded label.
- localized_component_id.
- localized_evidence_object_id, if applicable.
- evidence_gap_type: missing, stale, simulated_only, unsupported_claim, unreviewed, remediation_unvalidated, proxy_risk, monitor_disconnected, other, none_found.
- unsupported_claim_accepted: true, false, not_applicable.
- confidence_1_to_5.
- rationale_text.
- facilitator_notes.

Analysis fields to add after task completion:

- ground_truth_fault_ids.
- correct_decision: true, false, partial.
- detection_correct: true, false, partial.
- localization_correct: true, false, partial.
- false_assurance: true, false.
- rationale_support_level: supported_by_artifact, unsupported_inference, unclear.
- qualitative_error_theme.

## Debrief Questions

Ask each reviewer:

- Which artifact condition made evidence gaps easiest to find?
- Which artifact condition made it easiest to identify the responsible component?
- Which labels or fields were confusing?
- Did any artifact appear to imply fairness assurance beyond the evidence shown?
- What information would you need before approving the release?
- Were any task cards ambiguous or unrealistic?

## Ethics And Limitations

- The study uses synthetic systems only.
- The artifacts do not represent real deployments, real protected-class outcomes, or production monitoring.
- Reviewers should not be asked to make decisions affecting real people.
- Pilot findings are formative unless a formal human-subjects protocol, recruitment plan, consent process, and approval path are completed.
- Do not describe a small internal run as a controlled user study.
- Do not claim that the fairness evidence profile proves fairness.
- Do not claim that the fairness evidence profile improves reviewer performance before pilot data exists.
- Do not claim that FairMind produces production-validated fairness assurance from these fixtures.

## Reporting Boundaries

Allowed before pilot execution:

- "This protocol defines a formative pilot for comparing reviewability across baseline AI/ML BOM artifacts and a fairness evidence profile."
- "The task materials are designed to test detection of missing, stale, simulated, unsupported, or unreviewed fairness evidence in synthetic fixtures."

Allowed after a completed formative pilot, if supported by recorded data:

- "In this formative pilot, reviewers detected X of Y injected evidence faults under condition Z."
- "Observed errors suggest that reviewers missed or mislocalized the following evidence-gap themes."

Not allowed from this protocol alone:

- Claims that the profile proves fairness.
- Claims that reviewers generally perform better with the profile.
- Claims that the profile is a production-validated assurance mechanism.
- Claims that the pilot is a controlled study without a formal protocol and approval path.
