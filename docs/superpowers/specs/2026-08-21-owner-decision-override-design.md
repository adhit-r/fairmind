# Owner Decision Override Design

## Summary

FairMind will preserve genuinely independent evidence review and add one
separately gated owner-override path at the governance-decision boundary.
The override is atomic with the decision: the immutable decision row is the
single-use receipt, so there is no standing grant, expiry window, revocation
workflow, or transferable capability.

The override waives only the rule that the decider must differ from the run
requester and evidence submitters. It does not waive tenant scope, PostgreSQL
authority, run completion, accepted verified reviews, current evidence,
issuer/key/policy authority, exact evidence-set hashing, suite scope, verdict
version compare-and-swap, idempotency, or audit-chain requirements.

## Goals

- Keep evidence review four-eyes and permanently non-overridable.
- Correct the PostgreSQL review trigger so it independently rejects the
  submitter, evidence linker, and run requester, matching the application
  service.
- Allow only the canonical organization owner to make one explicitly
  justified governance decision when normal decision separation would reject
  that owner.
- Require both `evaluation:decision` and
  `evaluation:separation:override` from the persisted system owner role.
- Preserve the existing decision CAS, shared transactional unit of work,
  idempotency record, and per-organization audit hash chain.
- Keep the path default-off and PostgreSQL-authoritative.

## Non-goals

- Overriding evidence review or accepting self-reviewed evidence.
- Adding an expiring grant, bearer token, delegation, renewal, or revocation
  subsystem.
- Allowing an owner to authorize a different actor to consume an override.
- Enabling workers, automatic enforcement, unsupported modality packs, or a
  new frontend workflow.
- Making `evaluation:separation:override` assignable through legacy role,
  invitation, or membership-management APIs.
- Claiming protection from a compromised database schema-owner credential.

## Chosen Approach

### Atomic owner decision override

Add a distinct endpoint for an owner to create the decision and its override
receipt in the same audited transaction:

`POST /organizations/{org_id}/workspaces/{workspace_id}/systems/{system_id}/evaluation-v2/runs/{run_id}/decisions/owner-override`

The request contains the normal governance-decision fields plus one required
`ownerOverrideReason` string. The existing normal decision endpoint remains
unchanged and continues to reject override fields.

The decision's existing `owner_override_reason` column stores the bounded raw
justification. The public response exposes `ownerOverrideApplied: true` but
does not return the raw reason. Audit details contain a hash of the reason and
the exact waived relationships, not the raw reason.

This is the smallest complete model because the decision is already immutable,
versioned, tenant-scoped, and evidence-bound. Migration `013j` adds one
deferred PostgreSQL constraint trigger that requires each override decision to
have the matching completed shared-UoW idempotency record and immutable success
audit event at commit. A grant table would add standing authority and
issue/consume/revoke races without improving the approved same-owner action.

### Rejected alternatives

1. **Thirty-minute grant then consume.** This is warranted only when one owner
   authorizes another named actor. It adds a table, two mutations, expiry,
   revocation, and consumption races that the current requirement does not
   need.
2. **Override fields on the normal decision endpoint.** This weakens the normal
   path and makes accidental override use easier to authorize or replay.
3. **Review override.** This contradicts the four-eyes requirement and could
   let a submitter, linker, or requester validate their own evidence.

## Authorization

The route is available only when all three settings are true:

- `assurance_v2_enabled`
- `assurance_v2_governance_decision_enabled`
- `assurance_v2_separation_override_enabled`

The new setting defaults to `false`. The override router enforces all three
settings even when mounted directly in a test or alternate composition root.

The actor must satisfy every condition below inside the decision transaction:

1. The actor equals `organizations.owner_id` for the exact organization.
2. The organization is active.
3. The actor has an active `org_members` row for that organization.
4. The membership role is the exact system role named `owner`.
5. The matching `org_roles` row is marked `is_system_role = true`.
6. Its canonical JSON permission array contains at most 64 unique strings;
   every string is 1-128 characters and matches
   `^[a-z][a-z0-9_-]*(?::[a-z][a-z0-9_-]*)*$`.
7. The permission array contains both
   `evaluation:decision` and `evaluation:separation:override`.

The ordinary HTTP permission check still requires the normalized live
`evaluation:decision` permission. A narrow PostgreSQL-backed authorizer checks
the canonical owner and reserved override permission. General membership
normalization continues to omit the reserved permission, and legacy role APIs
continue rejecting attempts to create, invite, assign, or update a role with
it. Deployment must provision the system owner role explicitly; the migration
does not grant override authority to existing owners.

The only approved production provisioning path is a reviewed, per-organization
operator SQL/bootstrap change executed with the trusted schema-owner identity
under deployment change control. Runtime role, invitation, and membership APIs
cannot provision the reserved permission. Tests seed the same system-role row
inside isolated schemas. A general provisioning API or CLI is outside this
slice.

Role-name equality alone is never sufficient because legacy administrators
can assign role strings. Organization ownership is anchored by
`organizations.owner_id`. The PostgreSQL helper compares organization and actor
identifiers as text because deployed RBAC columns mix UUID and VARCHAR types;
it never casts caller governance identifiers to UUID.

The helper acquires row locks in one deterministic order: exact organization,
exact active membership, then exact system owner role. Both application
preflight and the insert trigger call the same locking helper. Missing rows,
deletes, status changes, owner changes, system-role changes, and permission
changes therefore serialize with the override and fail closed rather than
being validated against an unlocked snapshot.

## Evidence Review Invariant

Evidence review remains unchanged at the API and service boundaries: no
override field, reason, permission, route, or repository command is added.

The forward migration replaces the review insert guard so PostgreSQL loads the
exact run, admission, and link and rejects a reviewer equal to any of:

- `admission.submitted_by`
- `link.linked_by`
- `run.requested_by`

`separation_override_reason` must remain `NULL`. Existing review rows that
violate these rules cause the operator upgrade to fail closed; the migration
does not fabricate provenance or exceptions.

## Decision Flow

The owner-override service reuses the normal decision validation and shared
unit of work.

1. The router applies the master, decision, and override feature gates.
2. It requires normal `evaluation:decision` membership authorization and exact
   organization scope.
3. A strict request parser rejects duplicate, unknown, malformed, or oversized
   fields and requires a trimmed 1-2000 character `ownerOverrideReason`.
4. The shared unit of work claims the idempotency key, takes the organization
   advisory lock, and reads database time.
5. The repository locks the exact organization, membership, system owner role,
   and run authority.
6. The service checks canonical owner authority and every normal decision
   invariant.
7. The service derives the waived relationships from the locked authority.
   At least one of `run_requester` or `evidence_submitter` must apply; an
   independent owner must use the normal decision endpoint.
8. The repository inserts the decision with the bounded override reason.
9. PostgreSQL independently rechecks canonical owner authority, verifies the
   owner still equals the locked run requester or at least one exact evidence
   submitter, and waives only those requester/submitter identity comparisons.
10. The existing run-version CAS, audit append, idempotency completion, and
    outer commit finish in the same transaction. A deferred constraint then
    verifies the override decision's exact completed idempotency and immutable
    success-audit bindings before commit can succeed.

Strict HTTP parsing, feature-gate, permission, and other pre-UoW validation
failures create no idempotency claim or governance audit event. An expected
domain rejection inside the mutation callback rolls back business writes, then
commits the existing sanitized rejection audit and completed idempotency
response; an exact same-key replay returns that rejection and changed-body
reuse conflicts. An unexpected infrastructure failure rolls back the business
writes, audit event, and idempotency claim so a valid retry can proceed.

## Application And API Contract

The new request schema contains exactly:

- `expectedVerdictVersion`
- `overallVerdict`
- `layerVerdicts`
- `rationale`
- `ownerOverrideReason`

The normal validation limits, supported verdicts, suite-only layer authority,
and exact suite map remain unchanged. The override reason follows the database
limit of 1-2000 trimmed characters and the existing public-safe-string policy.

The owner-override response extends the normal decision response with the
literal marker `ownerOverrideApplied: true`. The normal decision response stays
unchanged, avoiding a compatibility change for completed idempotency records.
The raw override reason is not returned. Historical replay returns the exact
stored response and therefore retains the time-qualified decision result.

The override mutation uses a distinct operation string and audit action:

- idempotency operation:
  `evaluation-v2.governance-decision.owner-override`
- audit action:
  `evaluation_v2.governance_decision.owner_override_created`

The request hash binds the exact organization, workspace, system, run,
expected verdict version, decision payload, rationale, and override reason.

## Persistence And Migration

Add forward migration `013j`; do not edit frozen migrations `013` through
`013i`.

The migration adds no grant table and no decision column. It will:

- add one hardened PostgreSQL helper for canonical owner-override authority;
- add a permanent validated check that review
  `separation_override_reason IS NULL`;
- replace the review insert guard with submitter/linker/requester parity;
- replace the decision insert guard so a non-null `owner_override_reason` is
  accepted only for canonical owner authority;
- add one deferred constraint trigger that binds every override decision to
  its exact completed shared-UoW idempotency record and immutable success audit
  event at commit;
- keep update/delete denial and append-only decision/review semantics;
- fail upgrade on invalid existing review provenance;
- provide an operator upgrade, SQLite parity fixture, immutable checksums,
  startup catalog verification, and catalog digests.

The PostgreSQL authority helper validates organization, membership, system
role, canonical permission-array shape, and both literal permissions. It locks
the organization, membership, and role rows in that order with `FOR UPDATE`,
uses the trusted migration schema and a fixed hardened search path, and returns
false for any missing or malformed authority. Application preflight and the
decision trigger share this database predicate rather than implementing two
subtly different owner rules.

The decision trigger also derives the exact run requester and evidence
submitters. A non-null override reason is rejected unless the canonical owner
matches at least one of those actors, preventing direct SQL from recording an
override when normal separation already permits the decision.

The deferred constraint is scoped only to decisions whose
`owner_override_reason` is non-null. At transaction commit it requires exactly
one completed `governance_idempotency_records` row with the same organization,
owner actor, operation
`evaluation-v2.governance-decision.owner-override`, resource type
`evaluation_governance_decision`, and decision ID. Its canonical response
wrapper must name exactly one immutable `governance_evaluation_audit_events`
row with the same organization, actor, successful outcome, resource, and audit
action. The event's existing `_fairmindEvaluationSuccessBinding` must point
back to that idempotency record and repeat the same operation, action, resource,
and owner-override domain marker. The helper recomputes the canonical reason
hash and waived-relationship structure from the decision and relational graph
and requires the event details to match. This check is deferred because the
decision is written inside the callback before the shared unit of work appends
the audit event and completes idempotency. A raw decision insert without those
bindings fails at commit; normal decisions are unaffected. Later
idempotency-generation rollover does not erase the append-only audit event.

SQLite cannot establish the organization-role authority contract used for an
override. It continues to accept normal fixture behavior but rejects every
decision with a non-null owner override reason. Its review trigger enforces the
stronger submitter/linker/requester separation where the fixture graph permits
it.

## Audit Contract

The success audit retains the normal decision evidence and freshness fields
and adds:

- `ownerOverride: true`
- canonical owner actor ID
- exact run and verdict version
- canonical `waivedRelationships`, sorted by relationship type and actor, where
  each entry contains `relationshipType`, `actorId`, `resourceType`, and sorted
  unique `resourceIds`
- `ownerOverrideReasonHash`
- evidence-set hash
- database decision time

The audit never includes the raw override reason. Expected domain failures
raised from inside the shared mutation callback use the existing
rejected-mutation audit path. HTTP parsing, feature-gate, permission, and other
pre-UoW validation failures do not enter that governance chain. Unexpected
infrastructure errors roll back and are not represented as trusted governance
rejections.

`run_requester` entries use resource type `evaluation_run` and the exact run
ID. `evidence_submitter` entries use resource type `evidence_admission` and the
exact admission IDs submitted by the owner. The application derives this
structure from the locked authority, and PostgreSQL derives the same set for
the insert guard. Audit details also include the canonical SHA-256 of the
complete structure so a verifier can bind the human-readable entries without
guessing which admissions were waived.

## Error Contract

Errors remain bounded and reveal no cross-tenant authority details:

- disabled feature: 404 before service invocation;
- missing normal decision permission: existing 403;
- non-owner, inactive owner, malformed role permissions, or missing override
  permission: one generic 403 `evaluation_separation_override_forbidden`;
- independent owner with no separation conflict: 409
  `governance_decision_override_not_required`;
- stale version, evidence, scope, or run failures: existing decision errors;
- PostgreSQL owner-authority rejection: mapped to the same bounded 403;
- SQLite override attempt: bounded 409 PostgreSQL-authority-required error.

## Security Invariants

- Review override is impossible at every layer.
- Only the canonical active owner can use decision override.
- The reserved permission remains non-delegable through legacy APIs.
- Override waives only decider/requester and decider/submitter identity.
- PostgreSQL rejects an override when the owner is independent and the normal
  route could have created the same decision.
- Rejected, stale, unverified, unreviewed, wrongly scoped, or trust-invalid
  evidence remains ineligible.
- Exact evidence-set hash and verdict-version CAS remain mandatory.
- Same-key replay returns one stored response; changed-body reuse conflicts.
- Concurrent normal and override decisions produce one CAS winner.
- An override decision cannot commit without its exact completed idempotency
  record and immutable success-audit event; audit or persistence failure leaves
  no decision or partial override receipt.
- Cross-tenant identifiers return the same bounded not-found/forbidden shapes.

The existing shared database credential can supply actor text to direct SQL.
The trigger therefore proves relational owner authority for the supplied actor,
not the real-world identity controlling that credential. Containing a
compromised schema-owner/runtime credential requires the separately tracked
least-privilege runtime identity and protected actor-context work; this design
does not claim that protection.

## Verification

Implementation follows TDD. Required evidence includes:

### Application and route tests

- override route absent unless all three feature flags are true;
- direct-mounted router enforces all gates;
- normal route still rejects override fields;
- missing decision permission fails before service invocation;
- valid canonical owner succeeds only when a separation conflict exists;
- role-string owner, inactive membership, non-system role, malformed
  permissions, and missing either literal permission fail;
- unknown, duplicate, empty, unsafe, and oversized reason inputs fail;
- override cannot bypass any normal evidence, freshness, trust, scope, layer,
  or CAS validation;
- response and audit expose the marker/hash but not the raw reason;
- replay, changed-body conflict, rejected audit, and injected rollback retain
  the shared UoW guarantees.

### PostgreSQL and migration tests

- raw review inserts by submitter, linker, or requester fail;
- every review override field remains rejected;
- raw owner decisions without exact canonical authority fail;
- raw owner decisions with no requester/submitter conflict fail;
- valid system owner with both permissions succeeds;
- wrong owner, actor, organization, membership status, role, system-role flag,
  permission shape, or permission independently fails;
- cross-tenant and cross-scope substitutions fail;
- update/delete attempts on reviews and decisions fail;
- normal decisions remain valid without override authority;
- override versus normal-decision race produces one committed decision;
- permission or ownership mutation racing the override is serialized against
  the locked authority rows, including organization owner/active state,
  membership status/role, role system flag, permission-array changes, and row
  deletion;
- same-key concurrent override calls create one decision and one success audit;
- a raw override decision without the exact deferred idempotency/audit binding
  fails at commit, while the shared UoW path satisfies that binding;
- an injected infrastructure or commit failure after insert rolls back the
  decision and idempotency claim so the same key can retry, while an expected
  callback rejection commits and replays its stored rejection;
- direct/operator installation, replay, checksum, catalog, tamper, missing or
  disabled trigger, and startup verification pass on PostgreSQL 14;
- SQLite rejects override decisions and preserves review parity.

## Rollout Boundary

The endpoint remains disabled by default. Enabling it requires an explicitly
provisioned system owner role with both literal permissions and successful
PostgreSQL migration/startup verification. This internal control-plane feature
does not enable worker execution, automatic enforcement, certification,
compliance, or public `FairMind Verified` claims.
