# Idempotent mutation audit v1

Status: internal, default-off assurance control-plane contract

## Outcome

The evaluation workbench now binds both successful and expected-rejected
idempotent mutations to an exact immutable audit event. It records an expected
mutation rejection without committing the rejected business change. The
mutation unit of work holds the organization serialization lock, claims
idempotency, executes business work in a database savepoint, and then chooses
one terminal path:

- success: commit the business change, success audit event, and completed
  idempotency response atomically;
- expected rejection: roll back the savepoint, then commit one rejected audit
  event and the replayable rejected idempotency response atomically;
- audit or idempotency-finalization failure: roll back the outer transaction and
  return a generic persistence failure;
- unexpected exception: roll back the outer transaction without creating a
  potentially misleading expected-rejection event.

The authenticity service remains side-effect-free. Evidence admission will use
this shared mutation boundary later; no evidence is admitted by this change.

## Rejected event contract

The authoritative hash-chain event uses:

```text
action       evaluation_v2.mutation.rejected
outcome      rejected
resourceType evaluation_idempotency_key_hash
resourceId   SHA-256 idempotency-key hash
```

Its canonical `details` object is closed by the writer:

```json
{
  "schemaVersion": "evaluation-v2.rejected-mutation-audit/v2",
  "operation": "<server operation>",
  "requestHash": "<lowercase SHA-256>",
  "claimedAt": "<canonical idempotency-claim timestamp>",
  "expiresAt": "<claimedAt plus 30 days>",
  "errorCode": "<bounded stable code>",
  "statusCode": 422,
  "responseHash": "<SHA-256 of the canonical status-plus-body envelope>"
}
```

The raw request, raw idempotency key, error message, error details, exception,
signature, key material, result body, and credentials are not written to the
audit event. The replayable error is separately stored in the idempotency
record only after bounded safe-content validation. If that validation fails,
the caller and stored replay receive a generic rejection instead. The
idempotency record references the exact immutable audit-event ID. The claim and
expiry timestamps form the attempt generation. A reclaimed key receives a
claim timestamp strictly later than the preceding generation, even when the
wall clock repeats or moves backward. On replay, FairMind verifies the
organization chain once, point-loads the event by the trusted organization and
the row's exact audit-event reference, verifies every binding, and recomputes
the response digest before returning the error.

## Successful event and replay contract

Every successful mutation appends an event, including operations that
previously supplied no domain audit action. Those operations use the stable
`evaluation_v2.mutation.noop` integrity action. The event retains the actual
business resource type and ID and contains one closed binding object:

```json
{
  "_fairmindEvaluationSuccessBinding": {
    "schemaVersion": "evaluation-v2.success-idempotency-audit/v1",
    "auditEventId": "<event UUID>",
    "idempotencyRecordId": "<claim record UUID>",
    "idempotencyKeyHash": "<SHA-256>",
    "operation": "<server operation>",
    "requestHash": "<lowercase SHA-256>",
    "claimedAt": "<canonical idempotency-claim timestamp>",
    "expiresAt": "<claimedAt plus 30 days>",
    "resourceType": "<business resource type>",
    "resourceId": "<business resource ID>",
    "responseStatus": 201,
    "responseHash": "<SHA-256 of the exact bound success projection>",
    "action": "<event action>",
    "domainDetails": {}
  }
}
```

The idempotency row stores a private closed wrapper rather than the public
response directly:

```json
{
  "_fairmindEvaluationMutationSucceeded": true,
  "auditEventId": "<event UUID>",
  "responseBody": {}
}
```

The initial API result and a replay both expose only `responseBody`. The digest
binds the event ID, claim and expiry, business resource identity, 2xx status,
and exact public body. A replay requires the exact three-member wrapper,
verifies the organization chain, point-loads that event within the trusted
organization, checks its actor, action, outcome, resource and claim bindings,
and recomputes the digest. It never searches for a merely similar event.

Pre-contract completed-success rows contain no immutable response binding and
therefore fail closed as `idempotency_response_invalid`; FairMind does not
silently bless or backfill their mutable response. This also applies before an
expired completed row can be reclaimed. An operator must use a new
idempotency key until a separately reviewed legacy-retirement procedure exists.

Task 10 rejected records used the `/v1` event and response projections before
expiry was included in their immutable meaning. Task 11 writes `/v2` and fails
those older `/v1` records closed rather than silently redefining or upgrading
their history.

Every completed idempotency replay must be a bounded exact-canonical JSON
object with unique keys, finite I-JSON numbers, bounded depth and item count,
and a valid HTTP status. Alternate serialization, malformed content, array
roots, and unsafe numbers fail closed. Ordinary binding fields retain the
10,000-item ceiling. Success bodies and their wrapper use a larger item ceiling
derived from the 768 KiB response budget so a valid 32-suite plan response is
not rejected merely because it contains many small configuration values; the
byte and depth limits remain authoritative.

## Chain and transaction invariants

`append_evaluation_audit_event` verifies the existing organization chain before
every application append, calculates the event hash over the RFC 8785 canonical
projection, and inserts the event. Migration 013b database triggers enforce
that the event extends the current organization tail and atomically advance the
anchored head. The application never updates the head directly.

PostgreSQL uses the existing transaction-scoped organization advisory lock.
SQLite uses the existing process write lock and remains a parity fixture. No
migration changed: the existing event table already accepts `rejected` as an
outcome, and PostgreSQL 14 remains the release authority.

Successful and rejected responses are retained under the existing 30-day
idempotency policy. A retry with the same organization, actor, operation, key,
and request hash returns the bound result without executing the callback or
appending a second event. Before any completed row is reclaimed, its stored
expiry and immutable event binding are validated. Mutating `expires_at` cannot
force callback re-execution.

## Exact coverage boundary

This revision covers expected `EvaluationWorkbenchError` failures raised after
a trusted `MutationCommand` has entered the shared unit of work. It does not yet
cover:

- malformed HTTP or strict-JSON parser failures;
- unauthenticated requests or permission denials before trusted organization
  membership is established;
- domain normalization failures that occur before command construction;
- idempotency-key conflicts raised while claiming an existing different
  request;
- unexpected infrastructure exceptions, which roll back and surface a generic
  persistence failure.

Those paths require a trusted request-attempt boundary and, for unauthenticated
events, a separate security log that cannot be scoped by caller-controlled
organization data. Until that work lands, FairMind must not claim that every
rejected API request is present in the evaluation chain.

## Tamper boundary

The relational chain, immutable row triggers, runtime digest recomputation, and
anchored head detect ordinary row mutation, deletion, gaps, and disconnected
tails. They cannot detect a privileged attacker who deletes the entire chain
and head, or consistently rewrites every event and the head. An external
immutable/WORM checkpoint is required before claiming resistance to privileged
whole-chain replacement.

Optional request, correlation, IP, and user-agent columns are not part of the
current hash projection and the authoritative writer leaves them unset. They
must remain unset or be added through a new versioned projection before they
can be treated as integrity-protected evidence.

The internal chain still performs an O(n) organization-history verification on
replay. It will need checkpoints or another authenticated index before high
volume exposure. Domain audit details come from trusted application code but do
not yet have a dedicated secret-safe schema; callers must not place credentials,
raw private content, or reasoning traces in them. These constraints, and the
whole-chain replacement boundary above, remain release blockers for a public
evidence-integrity claim.

## Claim boundary

This is an internal control-plane integrity improvement. It does not enable an
evidence-admission route, a verified evidence state, reviewer acceptance, a
governance verdict, compliance, certification, automatic enforcement, or a
FairMind verification mark.
