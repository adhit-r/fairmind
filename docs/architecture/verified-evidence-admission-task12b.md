# Verified Evidence Passport V2 admission

Status: internal application kernel; route-composed but independently
default-off

## Purpose

Task 12B turns one authentic Evidence Passport V2 into one durable,
suite-specific evidence graph. It is the first application path that combines
the Passport contract, real Ed25519 verification, locked server authority,
transactional replay protection, database admission guards, and the existing
append-only mutation audit boundary.

The kernel admits supporting evidence only. A successful admission is not
reviewer acceptance, a governance verdict, framework compliance,
certification, a FairMind verification mark, or permission to enforce a
runtime decision.

## Trusted authority

The submitted Passport supplies an issuer key and signing-key identifier only
as lookup selectors. It cannot supply authoritative target, plan, suite,
envelope, policy, issuer, or key state.

`evaluatorId` is signed, stored, and receipt-bound. The internal admission
kernel resolves it through an installed durable evaluator-registration catalog,
locks an approved row in the same transaction as receipt persistence, and
requires the exact source, adapter name/version, result contract, issuer, and
signing-key binding. The registration ID and binding hash are included in the
append-only successful-admission audit event. Catalog administration has no
public route in this default-off slice; external and FairMind-worker
registration ceremonies and route-level catalog permissions remain separate
release gates. Product claims must not describe an evaluator or provider as
generally authorized until those gates exist.

Inside the organization-scoped mutation transaction, the trusted resolver:

1. locks the organization, workspace/system scope, evaluation run, every
   sibling suite execution, plan, target version, trust-policy version, every
   selected suite version, issuer, and exact signing key;
2. reads a fresh database clock rather than trusting the process clock;
3. reconstructs and verifies the complete immutable plan/run/envelope graph;
4. requires active plan, target, suite, policy, issuer, and signing-key state;
5. enforces issuer source, suite-version, and target-version restrictions;
6. requires an eligible signed source (`fairmind_worker` or
   `external_provider`) and Ed25519; and
7. derives the expected suite-specific execution binding from the stored
   envelope.

Empty issuer restriction arrays mean unrestricted for that dimension. A
malformed restriction, an unknown catalog reference, or a cross-scope
reference fails closed. Database row identities and public protocol identities
remain separate fields throughout the resolver and receipt.

The resolver hashes every admission-relevant authority fact. The service
resolves authority before authenticity assessment and again immediately before
persistence. Both hashes must match. This second check is defense in depth on
top of row locks and makes the verified receipt explicitly dependent on one
stable authority snapshot.

## Admission transaction

`VerifiedEvidenceAdmissionService.admit_verified_passport_v2` uses the existing
workbench unit of work. The idempotency request hash binds the operation, all
four scope identities, the raw Passport SHA-256 digest, and its byte length.
Raw document parsing and every rejection-capable decision occur inside the
mutation callback so expected 4xx failures receive one durable rejected audit
event and one replayable idempotency result.

The callback performs these steps:

1. Parse strict UTF-8 JSON with duplicate-key, non-finite-number, depth, node,
   and one-MiB limits.
2. Resolve the first locked authority snapshot.
3. Verify the content hash, exact tenant and execution binding, signature
   metadata, Ed25519 signature, key window, and Passport chronology using the
   fresh database time.
4. Match signed `sourceType`, `adapterName`, `adapterVersion`, and
   `resultContractVersion` to the locked plan and selected suite version.
5. Resolve authority again, require an identical authority hash, and use the
   second fresh database time as `verifiedAt`.
6. Calculate effective expiry exactly as the minimum of Passport expiry,
   `capturedAt + maximumEvidenceAgeSeconds`, and signing-key `validUntil`.
7. Require `verifiedAt` to be strictly earlier than effective expiry and
   require capture not to precede the envelope request.
8. Calculate the prospective selected-suite and parent-run result axes without
   collapsing evaluator execution failure into target failure.
9. Persist the complete graph, force deferred PostgreSQL receipt/admission
   constraints to immediate, append one success audit event, complete the
   idempotency record, and commit.

The callback allocates graph identities only after idempotency admission. An
exact replay returns the original response; it does not allocate or write a
second graph.

## Result-axis and multi-suite rules

Suite `technicalStatus` is evaluator execution health.
`evidenceResultStatus` is the evaluator's observation about the target. A
successful evaluator may report failed target evidence. A failed or timed-out
evaluator cannot produce a target pass. A cancelled evaluator may retain
`pending` evidence when it never produced a result.

One Passport updates one suite execution. It cannot complete other suites.
Until every suite has an eligible evidence link, the normal parent projection
remains preterminal with pending evidence even when evaluator processes have
already stored terminal-but-unlinked suite results. The last link computes the
exact technical and evidence aggregate across every sibling.

A selected suite that is already terminal but unlinked is eligible only when
the Passport result exactly matches its stored technical and evidence axes.
Its evaluator timestamps and failure projection remain immutable. A stored
terminal parent is accepted only when its axes equal the exact aggregate of all
locked siblings; a stale or partially aggregated terminal projection is
rejected.

Admission leaves suite review `pending`, freshness `current`, and the overall
governance verdict at its existing version-zero `insufficient` or `review`
state. Linking never produces `approved` or `blocked`.

## Atomic persistence graph

One successful first revision writes exactly:

- one `governance_evidence_runs` row;
- one complete canonical `governance_evidence_passport_revisions` row;
- one `governance_evidence_verification_receipts` row;
- one verified `governance_evidence_admissions` row;
- one immutable `governance_evidence_nonce_claims` row;
- one immutable `governance_evaluation_suite_evidence_links` row; and
- the selected suite projection, plus the parent run projection only when its
  result axes or evaluator timestamps actually change.

The receipt is intentionally inserted before the admission and closed through
the deferred 013c bidirectional constraints in the same transaction. The
service forces those constraints before reporting success. A partial graph,
nonce replay, occupied suite link, reused Passport revision, mismatched receipt,
or compare-and-swap conflict rolls the graph back.

For revision 1, `previous_revision_hash` is `NULL`. The evidence parent
`evidence_id` is also `NULL`. Evidence-run and revision `created_at` both equal
the database-derived verification time. These are explicit Task 12B metadata
semantics, not independent assurance facts.

Signed artifact descriptors remain authoritative only in the canonical
Passport snapshot and `artifact_refs_json`. Task 12B does not create normalized
artifact child rows. Artifact retrieval, quarantine, scanning, storage, and
descriptor reconciliation remain P1 prerequisites before artifacts can support
an assurance claim.

## Failure boundary

Expected contract, trust, authenticity, replay, occupancy, and relational
integrity failures are bounded 4xx application errors. Their private causes are
not returned. They commit only the rejected idempotency receipt and rejected
audit event; no evidence graph survives.

Only allowlisted PostgreSQL integrity SQLSTATEs and known 013b/013c constraint
messages become domain conflicts. Connection failures, operational database
errors, and unexpected post-write exceptions remain 500-class persistence
failures and roll back the graph, idempotency row, and audit event. This avoids
mislabeling infrastructure failure as a trustworthy user rejection.

## HTTP boundary

The verified-admission endpoint is mounted only when both the assurance-v2
flag and the independent evidence-submit flag are enabled:

`POST /api/v1/ai-governance/organizations/{org_id}/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/suite-executions/{suite_execution_id}/evidence`

The route requires the organization role permission
`evaluation:evidence:submit`. It binds the organization, workspace, system,
run, and suite execution path identities to the same immutable run projection
before reading the request body. It accepts only JSON media types and streams
at most the existing one-MiB request limit; the admission service receives the
raw bytes so canonical Passport parsing and authentication remain authoritative
inside the application transaction. Missing permission, any scope mismatch,
unsupported media type, and oversized bodies fail before an admission call.

The production composition uses real Ed25519 verification and the existing
transactional admission service, but its bootstrap evaluator registry is empty.
Therefore a flag-enabled deployment still rejects every evaluator as
unregistered until server-owned evaluator registration persistence and
approval ceremonies are released.

## Capability boundary

Task 12B deliberately adds no UI, worker, external-provider registration
ceremony, unsigned-import flow, reviewer action,
governance decision, framework mapping, certification, compliance claim, or
runtime enforcement. The kernel remains internal and default-off until its
native PostgreSQL adversarial suite, independent security review, and later
product release gates pass.

## Verification coverage

The Task 12B gate exercises the same terminal technical/evidence result matrix
through Passport normalization, application state verification, and the native
PostgreSQL `fairmind_suite_result_coherent` function. It also provisions a
complete second tenant and substitutes real foreign organization, system, run,
suite execution, target version, org-owned suite version, issuer, and signing
key identities. Every mixed-scope attempt must produce a bounded 4xx response,
zero evidence graph in both tenants, and zero successful admission audit.

Concurrency coverage includes twenty identical idempotent requests, distinct
Passport races for one suite, response-loss replay, key rotation, revocation
serialization, multi-suite linking, deferred-constraint corruption, and
unrelated native `23514` and `23503` failures after graph writes. Unexpected
database failures must leave zero graph, audit, and idempotency state.
