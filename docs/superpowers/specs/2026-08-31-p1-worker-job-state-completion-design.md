# P1 Worker Job-State and Signed Completion Design

## Decision

FairMind will keep `governance_evaluation_run_suite_executions` as the sole
logical job-state owner. A row in `governance_evaluation_suite_attempts` is the
immutable execution record for one lease attempt, not a second job. The parent
run is a derived aggregate of its suite-execution jobs.

For `fairmind_worker` delivery, a job stays `running` until one PostgreSQL
transaction proves the exact active worker, live lease, cancellation state, and
signed Evidence Passport V2 binding. That transaction verifies and persists the
Passport proof, creates the evidence link, and moves the attempt, suite
execution, and parent-run projection together. A worker cannot declare success
without that Passport.

Cancellation takes precedence at the transaction's serialization point. Once a
run- or suite-scoped cancellation request exists, start, heartbeat, retry, and
completion cannot advance the affected job. A success that committed before a
cancellation request was serialized remains immutable; cancellation is not a
retroactive rewrite of history.

`awaiting_evidence` remains a pre-execution state for `external_provider` and
`imported_report` delivery. It is not part of the worker-attempt lifecycle.

## Integration Base

This design is written against integrated branch commit `91bb612`, which
contains the P0 control-plane work, migration 013m, the leased PostgreSQL queue,
and the typed worker execution port. Commit `29eaba4` is the historical roadmap
starting reference, not an ancestor to transplant onto this branch. The
integrated branch is authoritative for implementation and verification.

## Goals

- Implement one coherent vocabulary for `queued`, `leased`, `running`,
  `awaiting_evidence`, `succeeded`, `failed`, `timed_out`, and `cancelled`.
- Add token-bound start, heartbeat, explicit failure, and expiry recovery for
  both leased and running attempts.
- Require a live lease and an exact verified signed Passport V2 before a worker
  job can become `succeeded`.
- Make cancellation, signed completion, attempt terminalization, the suite
  evidence link, and run aggregation atomic and race-safe.
- Preserve tenant, service-principal, worker-identity, envelope, suite,
  evaluator-registration, issuer, signing-key, and evidence freshness bindings.
- Preserve the P0 external/imported evidence workflows without allowing them to
  complete an active worker job.
- Keep PostgreSQL 14 as execution authority and SQLite fail-closed for worker
  mutations.

## Non-goals

- Mounting a public worker route or enabling `fairmind_worker` in preflight.
- Implementing a concrete evaluator, sandbox, artifact store, input broker,
  egress credential, kill switch, or operational metrics pipeline.
- Mounting a separate worker evidence-admission operation. Worker Passport
  admission and linking are part of the one completion transaction.
- Retrying evaluator-declared failures. Automatic retry in this slice is only
  for lease expiry while the frozen manifest retry budget remains.
- Allowing a worker to select its tenant, execution graph, result axes, run
  projection, timestamps, retry policy, or public failure message.
- Creating a second queue or job-state table.

## State Ownership

### Logical job

`governance_evaluation_run_suite_executions.technical_status` is authoritative
for one suite job. Queue ordering, retry budget, attempt count, result axes,
linked evidence, and public failure projection stay on this row.

### Attempt

`governance_evaluation_suite_attempts` proves which tenant-bound worker held a
specific lease and what happened to that lease. An active attempt mirrors its
job as `leased` or `running`. A terminal attempt remains immutable even when its
logical job is requeued for a later attempt.

### Parent run

`governance_evaluation_runs.technical_status` remains a derived projection. A
job transaction that changes a suite's technical or evidence-result state
recomputes the run from all locked sibling suite executions using the existing
aggregate priority. Heartbeat-only lease renewal does not recompute the run
because it changes neither projection. The run is never consulted as an
independent source of permission to alter an attempt.

### Pre-execution evidence

An `external_provider` or `imported_report` suite may remain
`awaiting_evidence` with `attempt_count = 0`. The verified-admission/link path
may terminalize an `external_provider` suite; the separately gated imported
evidence path may terminalize an `imported_report` suite. No worker attempt may
be created from `awaiting_evidence` directly.

An orchestrator-only dispatch operation may move an unlinked
`fairmind_worker` suite from `awaiting_evidence` to `queued` after validating
the immutable plan, suite, delivery mode, worker type, envelope, and absence of
cancellation. This operation is not mounted publicly in rows 81 or 82.

## State Protocol

| Current job | Operation | Attempt result | Job result | Required conditions |
|---|---|---|---|---|
| `awaiting_evidence` | external/imported evidence link | none | submitted terminal state | Delivery is not `fairmind_worker`; no attempt or cancellation exists |
| `awaiting_evidence` | internal worker dispatch | none | `queued` | Exact `fairmind_worker` plan/suite binding; unlinked and not cancelled |
| `queued` | claim | create `leased` | `leased` | Active matching worker, available time, retry budget, no cancellation |
| `queued` | cancellation | none | `cancelled` | Authorized append-only cancellation request |
| `leased` | start | `running` | `running` | Same tenant, principal, active worker, live matching token, no cancellation |
| `leased` | heartbeat | unchanged | unchanged | Same binding and live token; renew for 60 seconds |
| `leased` | explicit failure | `failed` | `failed` | Same binding and live token; server-owned failure projection |
| `leased` | expiry recovery | `timed_out` | `queued` or `timed_out` | Database lease expired; requeue only below frozen retry cap |
| `leased` | cancellation | `cancelled` | `cancelled` | Cancellation wins before any further worker progress |
| `running` | heartbeat | unchanged | unchanged | Same binding and live token; renew for 60 seconds |
| `running` | signed completion | `succeeded` | `succeeded` | Live token plus exact eligible signed Passport V2; no cancellation |
| `running` | explicit failure | `failed` | `failed` | Same binding and live token; server-owned failure projection |
| `running` | expiry recovery | `timed_out` | `queued` or `timed_out` | Database lease expired; requeue only below frozen retry cap |
| `running` | cancellation | `cancelled` | `cancelled` | Cancellation wins before evidence is linked |
| terminal technical state | worker/job transition | none | none | Rejected; terminal job and attempt technical state is immutable |

`awaiting_evidence` is therefore complete in the overall vocabulary but absent
from the worker-attempt transition graph. `succeeded` is reachable for an
attempted worker job only through signed completion.

Terminal immutability applies to evaluator-owned job facts: attempt and suite
technical status, evidence-result axis, completion/failure projection, and the
linked evidence identity. Existing P0 review decisions and freshness or
supersession projections may continue to evolve under their separate
authorities; they cannot rewrite those terminal evaluator facts.

### Deterministic terminal projections

The server owns the complete terminal projection. Worker input selects only an
allowed explicit-failure code:

| Cause | Evidence result | Failure code | Public failure message |
|---|---|---|---|
| evaluator execution failed | `error` | `worker_execution_failed` | `The evaluation worker could not complete the suite.` |
| evaluator output invalid | `error` | `worker_output_invalid` | `The evaluation worker produced an invalid result.` |
| resource budget exhausted | `unavailable` | `worker_resource_exhausted` | `The evaluation worker exhausted its assigned resources.` |
| evaluator dependency unavailable | `unavailable` | `worker_dependency_unavailable` | `A required evaluation dependency was unavailable.` |
| lease expired | `unavailable` | `worker_lease_expired` | `The evaluation worker lease expired.` |
| authorized cancellation | `unavailable` | `evaluation_cancelled` | `The evaluation was cancelled by an authorized user.` |

On recoverable expiry, the terminal attempt keeps the lease-expired pair while
the requeued suite returns to `evidence_result_status = pending` with null
failure fields. At retry exhaustion the suite receives the same lease-expired
pair. Cancellation reason text never becomes the public failure message. Parent
aggregation uses the existing technical-state priority and then ascending
`(ordinal, id)` to select the failure pair, so identical sibling states cannot
produce more than one legal run projection.

## Application Boundaries

The framework-free worker queue boundary expands with narrow commands and
receipts:

- `dispatch(scope)` is an internal orchestration command. It has no worker
  credential and no public route in this slice.
- `start(principal, credential)` changes exactly one leased attempt and job to
  running.
- `heartbeat(principal, credential)` accepts both leased and running attempts.
- `fail(principal, credential, failure_code)` terminalizes the exact active
  attempt and job. `failure_code` must be one of
  `worker_execution_failed`, `worker_output_invalid`,
  `worker_resource_exhausted`, or `worker_dependency_unavailable`; the server
  chooses the bounded public message. Arbitrary worker text is not persisted.
- `complete(principal, credential, raw_passport)` accepts the signed Passport
  as the completion proof. The input is bounded to the
  existing 1 MiB Passport maximum. The server derives all scope, status,
  timestamps, hashes, and result projections; no derived field is accepted
  separately from the worker.
- `recover_expired(limit)` is an internal scheduler seam with no public route.
  It scans leased and running attempts in bounded `SKIP LOCKED` batches, so
  recovery does not depend on another worker claiming work. Claim may still
  invoke the same helper opportunistically.
- `request_cancellation(actor, scope, reason, idempotency_key)` is a human
  Assurance V2 mutation. It requires the new live human permission
  `evaluation:run:cancel`; it never accepts or grants `evaluation:worker`.
- `bind_evaluator_registration(actor, worker_identity_id, registration_id)` is
  a human catalog-administration mutation. It requires the existing
  `evaluation:catalog:admin` permission and may set an identity's immutable
  registration binding exactly once before claim is allowed.

The queue and completion adapters own their transactions. They expose stable,
non-disclosing errors such as `worker_forbidden`, `worker_inactive`,
`lease_lost`, `job_cancelled`, `completion_conflict`, and
`worker_persistence_error`. A caller cannot distinguish a foreign attempt from
an expired, superseded, malformed, or unknown lease.

No public worker HTTP route is added by these rows. A later route must establish
`WorkerQueuePrincipal` from a service credential and must never accept the
organization or principal subject from request JSON.

Cancellation is exposed separately at:

`POST /organizations/{org_id}/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/cancellations`

The strict body contains `scopeKind`, optional `suiteExecutionId`, and a
trimmed 1-2000 character `reason`. `scopeKind = run` prohibits a suite ID;
`scopeKind = suite` requires the exact suite ID. The route requires
`evaluation:run:cancel`, exact active organization membership, the standard
Assurance V2 master gate, and an idempotency key. It returns the immutable
cancellation ID, scope, actor, database timestamp, and resulting run/suite
statuses, but not the raw reason. The audit stores a SHA-256 reason hash.

The worker-registration command is exposed under the existing default-off
evaluator-catalog gate at:

`PUT /organizations/{org_id}/evaluation-v2/evaluator-catalog/worker-identities/{worker_identity_id}/registration`

Its strict body contains only `evaluatorRegistrationId`. The transaction uses
the standard organization mutation unit of work, requires active membership
and literal `evaluation:catalog:admin`, and locks the worker identity,
registration, issuer, and signing key. It rejects a non-active worker, a
foreign, non-approved, revoked, or non-`fairmind_worker` registration, an
inactive issuer/key, any prior attempt, and any registration whose adapter
tuple is not compatible with the identity's server-loaded worker type and
capability snapshot. It never accepts worker type, adapter, issuer, or key from
the request. Repeating the exact binding is an idempotent read; attempting to
replace it conflicts. The audit action is
`evaluation_v2.worker.evaluator_registration_bound` and contains IDs and the
registration binding hash, not credentials or key material.

## Start, Heartbeat, Failure, and Recovery

Every worker mutation uses PostgreSQL `clock_timestamp()`. It locks and proves:

1. the exact organization and run scope;
2. the selected suite-execution job;
3. the exact active attempt named by the credential;
4. the worker identity bound to the authenticated service subject;
5. the absence of run- or suite-scoped cancellation;
6. the expected job and attempt states; and
7. a constant-time match between the supplied token hash and the stored hash.

Start requires both rows to be `leased`, sets the same database timestamp as
`started_at`, and advances both to `running`. Heartbeat renews an otherwise
unchanged leased or running attempt for exactly 60 seconds and returns the
20-second heartbeat hint. A worker identity disabled or revoked after claim
cannot start, heartbeat, fail, or complete.

Explicit failure accepts only a server-defined code and maps it to a sanitized
operator-safe message. It changes an active attempt and its job to `failed` in
one transaction. It does not retry and cannot attach evidence.

Expiry recovery locks the job and attempt, rechecks expiry using database time,
and terminalizes the attempt as `timed_out`. If `attempt_count < max_attempts`,
the job returns to `queued`, clears `started_at`, keeps its immutable attempt
history, and becomes available at the recovery timestamp. Otherwise the job
becomes `timed_out` with the lease-expired terminal projection. The parent run
is recomputed in the same transaction.

Because migration 013m allowed retry only from `leased`, forward migration 013n
must add a narrowly guarded `running -> queued` recovery transition. The suite
guard permits it only when the latest attempt has just become `timed_out`, its
number equals `attempt_count`, retry budget remains, no cancellation exists,
and no active attempt remains. The corresponding run transition is allowed
only when it is the exact aggregate of its locked suite rows. Migration 013n
also narrows the queue-metadata guard so `available_at` may change during this
one validated recovery transition; every other non-queued change remains
rejected. No general caller may use `running -> queued` as a reset.

Claim must validate more than `worker_type`. The immutable worker capability
snapshot must include the envelope's execution depth and lifecycle phase before
the candidate is leased. A matching type with insufficient declared capability
is skipped, not delivered and rejected after disclosure.

## Signed Completion

Completion accepts the bounded raw signed Passport and the lease credential in
one operation. It reuses extracted pure validators and persistence helpers from
the verified-admission and verified-link pipelines, but it does not call either
transaction-owning service. The completion transaction parses the I-JSON,
verifies Ed25519 authenticity, locks trusted authority, validates chronology,
reconstructs the server execution binding, checks the evaluator registration,
and persists the admission, revision, verification receipt, nonce claim, and
link before terminalizing the worker state.

The credential's attempt ID selects the database authority. Organization, run,
suite, and worker scope are derived from that locked graph; unverified Passport
fields are never used to choose which tenant or job to load. The canonical
service principal becomes `submitted_by`, `linked_by`, and the completion audit
actor.

To preserve the parent-before-child lock order, the repository may perform one
non-authoritative locator read using `(organization_id, attempt_id)`, then lock
the derived system, run, and suites before reloading the attempt. Every locator
field must match the locked graph; a missing or changed row returns the same
non-disclosing lease error.

The Evidence Passport V2 execution-binding contract gains three fields that are
required only when `deliveryMode` is `fairmind_worker` and prohibited for the
other delivery modes:

- `attemptId`: the exact UUID of the leased attempt;
- `attemptNumber`: the immutable attempt number; and
- `workerIdentityId`: the exact tenant-bound worker identity.

These fields are part of the signed content and expected-binding hash. No lease
token or token hash enters the Passport. A Passport signed for an expired prior
attempt therefore cannot complete a later retry, even if its suite, envelope,
and evaluator registration are otherwise identical.

Worker identities gain an immutable `evaluator_registration_id` binding before
row-81 claim is enabled. The Passport evaluator, trusted issuer/key, and
verified registration must resolve to that exact registration. Worker type
alone is not sufficient identity proof.

The completion transaction must require all of the following:

- the job and attempt are both `running`;
- the database clock is strictly before `lease_expires_at`;
- the authenticated organization and service subject resolve to the same
  active worker identity stored on the attempt;
- the raw token has canonical shape and its SHA-256 matches in constant time;
- neither a run- nor suite-scoped cancellation request exists;
- the Passport result technical status is exactly `succeeded`;
- its `evidenceResultStatus` is one of the existing succeeded-state values:
  `passed`, `passed_with_limitations`, `failed`, `informational`,
  `insufficient_data`, or `unknown`;
- the signed worker binding matches the attempt ID, attempt number, and worker
  identity, in addition to the organization, workspace, system, run, suite
  execution, envelope ID, envelope hash, envelope nonce, plan, target, trust,
  manifest, and configuration hashes;
- `started_at <= capturedAt <= signedAt <= database now < lease_expires_at`;
- the canonical Passport content, signature input, snapshot, execution binding,
  and evaluator projection hashes recompute exactly;
- the plan, trust policy, suite version, issuer, and signing key remain active,
  while the evaluator registration remains approved and exactly matches the
  worker identity;
- the Passport delivery source is `fairmind_worker` and its suite adapter,
  adapter version, result contract, manifest digest, and configuration hash are
  the exact immutable suite binding; and
- the Passport artifact list is empty until the later content-addressed storage
  row provides finalized, attempt-bound artifact authority.

After all checks pass, the same transaction performs these writes in order:

1. insert the immutable evidence run, Passport revision, verification receipt,
   nonce claim, and verified admission graph;
2. insert the single immutable suite evidence link;
3. set the attempt to `succeeded`, bind its evidence run, Passport revision,
   and suite evidence link, and set `completed_at`;
4. set the suite execution to `succeeded`, copy the validated result axes,
   summary, limitations, and evidence-link projection, and set `completed_at`;
5. recompute and update the parent run projection from all locked siblings; and
6. append one `evaluation_v2.worker.completion_succeeded` audit event for
   resource type `evaluation_suite_attempt` before commit.

Any error rolls back every write. In particular, there is no state where an
attempt succeeded without a link, a suite linked without a succeeded attempt,
or a parent run reflects a result that did not commit.

The implementation must extract reusable pure validation and persistence
helpers from the existing verified-admission and verified-link code. It must not
call `VerifiedEvidenceAdmissionService.submit_verified_passport_v2()` or
`VerifiedEvidenceLinkService.link_verified_evidence()` as nested operations,
because those services own independent idempotency/audit transactions and the
link service can currently mutate suite and run projections independently.

## Canonical Run Arbiter

Every dispatch, claim, start, heartbeat, explicit failure, expiry recovery,
worker completion, external verified-link terminalization, imported-evidence
terminalization, and cancellation transaction serializes on one run-scoped
PostgreSQL advisory transaction lock before taking relational mutation locks.
The lock identity is the signed 64-bit result of:

```sql
pg_catalog.hashtextextended(
  'fairmind:evaluation-run:v1|'
  || length(org_id)::text || ':' || org_id
  || '|' || length(run_id)::text || ':' || run_id,
  0
)
```

Blocking operations pass that value to `pg_advisory_xact_lock`; claim uses
`pg_try_advisory_xact_lock` so a busy run does not stall unrelated queue work.
The organization and run IDs are server-loaded canonical database identifiers,
never raw Passport or request-body scope. A 64-bit hash collision only causes
safe extra serialization: every operation still locks and revalidates the exact
relational organization/run graph, so the advisory key grants no authority.

All current operations touch one run. Any future transaction that must touch
multiple runs must sort unique `(organization_id, run_id)` tuples
lexicographically and acquire their arbiter keys in that order. This is the
global order across organizations and runs.

## P0 Evidence-Link Compatibility

The ordinary verified-evidence link path will be narrowed as part of migration
and service work:

- it may transition an unattempted `awaiting_evidence` suite for
  `external_provider` delivery;
- the imported-report service keeps its separately gated imported-evidence
  authority only for an unattempted `awaiting_evidence` suite;
- both existing evidence paths reject `queued`, `leased`, and `running` suites;
- both acquire the canonical run arbiter and reject run- or suite-scoped
  cancellation before persisting admission, link, or terminal projections;
- it rejects any suite with `attempt_count > 0`, including a terminal worker
  suite; and
- it cannot create or update a worker attempt.

Worker completion is the only authority allowed to link evidence to an
attempted suite. This removes the current ambiguous path in which the ordinary
link service accepts `queued`, `leased`, and `running` suites.

## Cancellation Arbitration

Cancellation is an append-only request and an atomic state transition, not a
best-effort signal. An authorized cancellation operation acquires the same
canonical run arbiter and row locks as worker mutations, inserts the unique
run- or suite-scoped cancellation row, terminalizes every affected active
attempt, terminalizes each non-terminal suite job, and recomputes the parent
run before commit.

For run cancellation, suite locks are acquired in ascending `(ordinal, id)`
order. Suites are changed before the parent run so the existing parent guard
cannot leave a cancelled run with advancing children.

After acquiring its locks, every dispatch, claim, start, heartbeat, failure,
recovery, completion, external verified-link, and imported-evidence operation
rechecks cancellation. If a cancellation row exists, the operation cannot
advance state or persist evidence. Completion must not insert an evidence link
and returns the stable cancelled result. Already-terminal evaluator/job facts
remain immutable. A suite-scoped cancellation against a terminal job, or a
run-scoped cancellation after every suite is terminal, is rejected without
inserting a cancellation row. In a mixed run, already-terminal siblings whose
`completed_at` is strictly earlier than the database-owned `requested_at`
remain historical while every non-terminal sibling is cancelled.

The linearization point is acquisition of the canonical run arbiter followed
by the locked cancellation check. A cancellation that acquires the arbiter
first and commits its request wins. A completion committed before cancellation
acquires the arbiter is historical success, not an in-flight race. Absolute
priority between two operations that have not yet acquired the arbiter is not
claimed.

## Lock Order and Concurrency

State-changing operations use one deterministic order:

1. existing organization advisory transaction lock, where the shared mutation
   unit of work applies;
2. the human cancellation idempotency claim, for that operation only;
3. the canonical run transaction arbiter defined above;
4. exact system scope and parent run;
5. every required suite execution in ascending `(ordinal, id)` order;
6. selected active attempt;
7. bound worker identity;
8. run-scoped then suite-scoped cancellation records;
9. plan, target, trust policy, suite version, issuer, signing key, and evaluator
   registration; and
10. conflicting admission, nonce, Passport, evidence-link, and audit identities
   before their immutable inserts.

The database clock is read after lock waits, immediately before lease,
chronology, freshness, and cancellation validation. A timestamp read before a
blocking lock is not authority for completion.

Worker state and completion operations do not use the generic idempotency
claim. Human cancellation does, so its existing idempotency row is acquired
before the canonical run arbiter and completed with the cancellation audit in
the same transaction.

Claim uses a two-phase locator protocol rather than locking a suite before its
run arbiter. A bounded, non-authoritative read returns candidate run locators in
queue order without returning an envelope or worker payload. Each candidate is
tried in a fresh transaction: derive and try the canonical run arbiter; lock
the exact system and parent run (`FOR UPDATE SKIP LOCKED`); lock all sibling
suites in ascending `(ordinal, id)` order; lock the worker identity and
cancellation rows; then select and revalidate the earliest eligible suite
inside that locked run. Capability, availability, retry, registration, and
cancellation predicates are repeated under the locks before the attempt and
lease token are created. A busy or changed candidate rolls back without a
mutation and the locator proceeds to another run. A claim never accumulates
multiple advisory locks in one transaction.

Dispatch, claim, start, failure, expiry recovery, completion, P0 evidence
terminalization, and cancellation recompute the stored parent projection after
their suite transition. Heartbeat retains the same run state but still uses the
arbiter and exact locks so cancellation cannot race lease renewal. Run-level
cancellation locks every sibling suite in ascending `(ordinal, id)` order.
Existing evidence authority loading will be refactored into helpers that assume
the earlier scope locks already exist; completion will not invoke a second
transaction-owning service.

PostgreSQL serialization or deadlock failures may retry the entire transaction
a small bounded number of times. Individual statements are never retried after
partial application, and an already-committed terminal result is never
re-executed.

## Idempotency and Replay

The terminal attempt, its exact `suite_evidence_link_id`, and the linked
verification receipt's Passport content, canonical snapshot, and signature
input hashes are the completion idempotency authority; the generic
product-mutation replay path is not used.

That generic unit of work resolves replay before its callback and therefore
cannot prove the lease token on an exact retry.

The first successful completion requires a live lease. In one new transaction,
a transport retry after commit may return the existing receipt only after it
locks the terminal attempt and proves the same authenticated organization and
service subject, currently active worker identity, canonical raw token, attempt
ID, admission ID, Passport revision ID, Passport content hash, and immutable
result binding. The IDs are derived from the committed terminal graph, not
accepted as extra retry input; the canonical snapshot and signature input
hashes must also match. This replay performs no mutation and does not
reinterpret an expired lease as new authority. Disablement or revocation makes
the historical receipt unavailable through the worker replay boundary.

A changed raw Passport, result, principal, token, or scope after terminalization
returns `completion_conflict` or the non-disclosing lease error. Two concurrent
completion requests can create only one evidence graph, link, and terminal
transition. A success audit is appended once.

The raw lease token is never stored in audit details, logs, metrics, exceptions,
or responses beyond the original lease credential. Audit details bind the
attempt and evidence identities, not the raw token.

## Database Enforcement

Frozen migrations 013 through 013m are not edited.

### Migration 013n: job-state protocol

Migration 013n will add the guarded running-attempt recovery transition and
commit-time graph assertions for worker jobs:

- worker identities gain a nullable migration-compatibility
  `evaluator_registration_id` with an exact tenant foreign key;
- the catalog-admin binding command may set that field once, only while the
  identity has no attempt, after the approved registration and active
  issuer/key checks described above;
- `attempt_count = 0` permits the existing unattempted external/imported flow;
- a `leased` or `running` attempted job has exactly one active attempt with the
  same status and attempt number;
- a requeued attempted job has no active attempt and its latest attempt is
  `timed_out`;
- an attempted terminal job has a matching latest terminal attempt;
- `failed`, `timed_out`, and `cancelled` attempts require their exact
  server-owned failure-code/message pair;
- attempted worker jobs cannot enter `succeeded` until migration 013o installs
  the signed-completion authority; and
- direct state changes that do not satisfy the graph fail at commit.

It also updates the queue metadata guard for the single validated recovery
case and makes the internal recovery sweep independently callable. Claim checks
worker type, execution depth, lifecycle phase, and the immutable approved
registration binding against the capability snapshot before lease creation.
Claim skips an identity whose registration is null, no longer approved, or no
longer backed by active issuer/key authority. The migration never invents a
registration for an existing worker, so no row-81 attempt can strand an
unregistered identity before signed completion arrives.

It will provide PostgreSQL operator upgrade, frozen ledger/catalog updates,
SQLite structural parity, and SQLite worker-write denial.

### Migration 013o: signed completion and cancellation precedence

Migration 013o will:

- extend the Passport V2 execution-binding schema and canonical builders with
  conditional `attemptId`, `attemptNumber`, and `workerIdentityId` fields for
  `fairmind_worker` only;
- add immutable `suite_evidence_link_id` authority to succeeded attempts, with
  a composite foreign key covering run, suite execution, evidence run, Passport
  revision, workspace, system, and organization; and
- replace the temporary success denial with deferred graph constraints.

Those constraints require every succeeded attempted job to have a latest
succeeded attempt; identical evidence-run, Passport-revision, and suite-link
IDs on the attempt and suite graph; exactly one verified, current admission and
verification receipt; matching attempt, worker, nonce, envelope, and canonical
Passport hashes; and exactly one immutable successful worker-completion audit
event.

The migration-013n worker-registration column remains nullable only for
compatibility, but migration-013n claim already skips an identity without an
eligible binding. Start and completion reject a missing, changed, revoked, or
otherwise ineligible registration. A bound registration remains immutable
after its first assignment even if no attempt exists; operators replace the
worker identity rather than retargeting its evaluator authority.

The Passport contract remains version `2.0.0` because `fairmind_worker` is
still default-off and has never been a released ingress. Existing
`external_provider` Passports keep their current shape and must not carry the
worker-only attempt fields.

It will also enforce cancellation precedence. A suite-scoped cancellation may
be inserted only for a non-terminal suite. A run-scoped cancellation requires
at least one non-terminal suite. After insertion, an affected non-terminal
suite or active attempt must be `cancelled` before commit; earlier terminal
siblings in a mixed run remain unchanged. The same rule applies to every suite
covered by a run-scoped request.

The application remains responsible for authenticated principal and raw-token
proof because PostgreSQL stores only the token hash. Database constraints remain
responsible for relational scope, transition, evidence, and append-only
integrity even if application code is bypassed.

## Audit and Disclosure

Claim and heartbeat use the attempt row as operational history; heartbeats do
not append high-volume governance audit events. Dispatch, explicit failure,
signed completion, and cancellation append bounded governance audit events:

- `evaluation_v2.worker.job_dispatched`;
- `evaluation_v2.worker.attempt_failed`;
- `evaluation_v2.worker.completion_succeeded`; and
- `evaluation_v2.worker.cancellation_requested`.

Completion audit details include the organization, run, suite execution,
attempt, worker identity, admission, evidence run, Passport revision, Passport
content hash, terminal status, and timestamps. They exclude raw tokens,
credentials, raw Passport bytes, arbitrary worker diagnostics, artifact
payloads, secrets, and chain-of-thought.

Worker-facing errors remain stable and non-disclosing. User-facing failure text
comes from server-owned mappings. Protected operational logs may reference
opaque correlation IDs but must not contain the lease credential.

## Verification Strategy

Implementation proceeds by TDD in two roadmap rows. Row 82 is delivered as
three separately reviewable prerequisite, completion, and cancellation
subplans; the roadmap row is checked only after all three pass.

### Row 81: job states

- catalog-admin worker-registration binding route, permission, exact replay,
  cross-tenant, inactive authority, incompatibility, and immutability tests;
- port contract tests for dispatch, start, leased/running heartbeat, explicit
  failure, and stable errors;
- PostgreSQL tests for exact state pairs and parent aggregation;
- wrong tenant, service subject, worker identity, token, status, and expired
  lease rejection;
- disabled/revoked worker rejection after claim;
- leased and running expiry recovery below and at retry cap;
- independent scheduled recovery without a subsequent claim;
- capability mismatch for execution depth or lifecycle phase is skipped before
  envelope disclosure;
- direct-SQL attempts to reset running or terminal jobs rejected;
- concurrent start, heartbeat, recovery, and claim tests; and
- unchanged default-off route and preflight assertions.

### Row 82: completion and cancellation

- cancellation route, strict-body, permission, tenant-scope, idempotency,
  reason-redaction, and audit-hash tests;
- independent mismatch tests for tenant, subject, identity, token, expiry,
  attempt/job status, cancellation, admission, receipt, nonce, envelope ID,
  envelope hash, envelope nonce, canonical Passport snapshot, Passport content
  hash, issuer, key, evaluator registration, adapter, contract, and freshness;
- proof that only a `succeeded` signed Passport can produce worker success;
- otherwise-valid signed success with an invalid or unavailable evidence-result
  axis rejected;
- stale prior-attempt Passport, attempt-number, worker-identity, registration,
  chronology, and non-empty artifact-list rejection;
- cancellation-versus-start, cancellation-versus-completion,
  cancellation-versus-external-link, cancellation-versus-imported-link,
  recovery-versus-completion, and double-completion barrier tests;
- exact replay succeeds without a second mutation; changed replay fails closed;
- rollback tests at every write boundary prove no partial attempt, link, suite,
  run, idempotency, or audit state;
- direct ordinary evidence linking to queued, leased, running, or attempted
  terminal worker jobs rejected;
- PostgreSQL 14 migration replay, two-install catalog digest, privilege,
  enabled-always trigger, and native mutation tests; and
- SQLite parity objects present while all worker mutations remain unavailable.

Focused tests are followed by the complete affected backend suites, PostgreSQL
14 migration/integrity suites, layer-boundary checks, archive-import checks,
Python compilation, and `git diff --check`. Green focused checks do not claim a
worker route, evaluator runtime, sandbox, artifact store, broker, egress policy,
or production readiness.

## Implementation Order

1. Implement migration 013n, the registration-binding prerequisite, and row-81
   state operations by TDD.
2. Row 82a: narrow the P0 link paths, extend the Passport contract, add the
   attempt/link schema authority, and install deferred graph constraints.
3. Row 82b: implement unified completion persistence and exact replay, then
   prove rollback at every write boundary.
4. Row 82c: implement the cancellation permission, route, arbitration, and
   cross-operation race tests.
5. Run security diff review and fresh PostgreSQL verification after each
   reviewable subplan, followed by the full row-82 gate.
6. Update the roadmap only when each complete row's contract and evidence pass.

Artifact storage, opaque brokers, sandbox execution, and egress/metrics remain
separate later P1 designs and cannot claim completion from this work.
