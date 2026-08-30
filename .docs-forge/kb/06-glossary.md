# P0 glossary

| Term | Meaning in the P0 documentation | Source |
| --- | --- | --- |
| Admission | The persisted result of checking a submitted Passport against exact scope, envelope, evaluator, issuer, key, policy, replay, and chronology requirements. It is not yet linked or reviewed. | `apps/docs/content/docs/evidence-trust-review.mdx:L8-L25` |
| Assurance V2 | The internal, default-off contract and route family documented by this alpha. It is not a stable public API. | `.docs-forge/answers.json`; `apps/backend/api/main.py:L381-L502` |
| Decision evidence eligibility | A derived indication that specific evidence is currently acceptable for a governance decision under persisted trust and freshness facts. It is not a safety or compliance score. | `apps/docs/content/docs/evidence-trust-review.mdx:L35-L49` |
| Evidence Passport V2 | A closed evidence payload and signature projection submitted for exact server-side admission checks. | `apps/docs/content/docs/evidence-trust-review.mdx:L8-L18` |
| Execution envelope | The immutable scope and hash binding for a particular run and suite execution. | `apps/docs/content/docs/assurance-workflow.mdx:L8-L31` |
| Four-eyes review | The rule that a reviewer cannot be the run requester, evidence submitter, or evidence linker. There is no review override. | `apps/docs/content/docs/evidence-trust-review.mdx:L26-L34` |
| Freshness | A state derived at database time from receipt, evaluator, issuer, key, policy, review, expiry, revocation, and supersession facts. | `apps/docs/content/docs/evidence-trust-review.mdx:L35-L49` |
| Governance decision | A separately authorized, immutable decision record bound to eligible evidence and a bounded rationale. It is distinct from technical status and evidence review. | `apps/docs/content/docs/assurance-workflow.mdx:L20-L31` |
| Link | The separate mutation that connects one admitted Passport revision to one exact suite execution. | `apps/docs/content/docs/evidence-trust-review.mdx:L20-L29` |
| P0 | The trustworthy control-plane and frontend/design foundation represented by this alpha release boundary. It does not include workers or real evaluation engines. | `README.md:L18-L53` |
| Preflight | A check of plan state and blockers. It does not create or imply an execution. | `apps/docs/content/docs/assurance-workflow.mdx:L42-L50` |
| Separation exception | A separately gated, audited decision path for an actual decision-separation conflict. It does not alter review separation or other decision invariants. | `apps/docs/content/docs/permissions-and-separation.mdx:L30-L49` |
| Technical status | The recorded state of a suite execution. It must not be collapsed with evidence result, admission, review, or freshness. | `apps/docs/content/docs/assurance-workflow.mdx:L33-L41` |
| Worker principal | A tenant-bound service principal carrying the reserved `evaluation:worker` permission. P0 exposes no worker route, credential issuer, or runtime. | `apps/backend/src/api/evaluation_permissions.py:L33-L35`; `apps/backend/src/api/evaluation_permissions.py:L86-L128` |
