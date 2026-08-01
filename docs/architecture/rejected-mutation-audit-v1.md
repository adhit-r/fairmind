# Rejected mutation audit v1

Status: internal, default-off assurance control-plane contract

## Outcome

The evaluation workbench now records an expected mutation rejection without
committing the rejected business change. The mutation unit of work holds the
organization serialization lock, claims idempotency, executes business work in
a database savepoint, and then chooses one terminal path:

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
  "schemaVersion": "evaluation-v2.rejected-mutation-audit/v1",
  "operation": "<server operation>",
  "requestHash": "<lowercase SHA-256>",
  "claimedAt": "<canonical idempotency-claim timestamp>",
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
idempotency record references the exact immutable audit-event ID. The claim
timestamp is the attempt generation and changes when an expired key is
reclaimed, so historical rejection events cannot collide with a later attempt.
On replay, FairMind verifies the organization chain, locates the rejection by
organization, actor, operation, request hash, claim timestamp, and
idempotency-key hash, checks that exact event reference, and recomputes the
response digest before returning the error.

Every completed idempotency replay, including success responses, must be a
bounded exact-canonical JSON object with unique keys, finite I-JSON numbers,
bounded depth and item count, and a valid HTTP status. Alternate serialization,
malformed content, array roots, and unsafe numbers fail closed.

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

Rejected responses are retained under the existing 30-day idempotency policy.
A retry with the same organization, actor, operation, key, and request hash
rethrows the stored rejection without executing the callback or appending a
second event.

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

Successful idempotency responses now receive strict structural/canonical
validation on replay, but their status and body are not yet digest-bound to the
success audit event. A privileged edit to a valid canonical success response
therefore remains detectable only through database controls outside this
contract. Success-response binding is required before this path can support a
public evidence-integrity claim.

## Claim boundary

This is an internal control-plane integrity improvement. It does not enable an
evidence-admission route, a verified evidence state, reviewer acceptance, a
governance verdict, compliance, certification, automatic enforcement, or a
FairMind verification mark.
