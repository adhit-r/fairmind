# Reviewer Task Cards

Use these cards for formative review of FairMind synthetic fixtures only. Do not describe results from these cards as a controlled user study unless a formal protocol and approval process exist.

Each reviewer should answer:

- Decision: approve, reject, or request more evidence.
- Risk found.
- Responsible component.
- Evidence missing or stale.
- Confidence from 1 to 5.
- Short rationale.

## Loan Approval Model

### Task L1: Release Readiness

You are reviewing the loan approval release package. Decide whether the system has enough fairness evidence for release approval.

Expected focus: stale evaluation evidence, unsupported regulatory claim, missing reviewer approval.

### Task L2: Protected Attribute Coverage

You are reviewing whether the loan model tested all claimed protected attributes and relevant proxies.

Expected focus: caste/category proxy, low-resource language, and older applicant coverage gaps.

### Task L3: Remediation Credit

You are reviewing whether the threshold adjustment can be credited as a mitigation.

Expected focus: no post-remediation fairness metric and untested validation state.

### Task L4: Proxy Risk

You are reviewing whether feature engineering creates fairness risk not visible in a generic BOM.

Expected focus: postal region and occupation category as proxy features.

## Hiring Ranker

### Task H1: Release Readiness

You are reviewing the hiring ranker release package. Decide whether release approval is supported.

Expected focus: missing disability and non-English evidence, stale evaluation, and missing approval.

### Task H2: Historical Labels

You are reviewing whether the training data can support fairness claims.

Expected focus: biased historical interview labels and missing subgroup coverage.

### Task H3: Remediation Credit

You are reviewing whether feature deweighting can be credited as a bias mitigation.

Expected focus: no post-remediation top-k ranking test.

### Task H4: Monitoring

You are reviewing whether deployment monitoring can detect the fairness risks identified upstream.

Expected focus: absent live applicant outcome feed and monitor coverage gaps.

## Healthcare Triage Model

### Task C1: Release Readiness

You are reviewing a high-risk clinical triage release package. Decide whether the system can be approved.

Expected focus: missing current evaluation set, disconnected monitor, and unsupported release claim.

### Task C2: Population Shift

You are reviewing whether model evidence supports the shifted deployment population.

Expected focus: rural and non-English patients not covered by current evidence.

### Task C3: Evaluation Evidence

You are reviewing whether the fairness evaluation set is adequate.

Expected focus: evaluation set version is missing and no current subgroup metrics exist.

### Task C4: Monitoring

You are reviewing whether the live monitor can detect fairness drift.

Expected focus: monitor has no live outcome feed and excludes region and language.
