# Delegated Separation-Override Grant Design

## Decision

FairMind adds a short-lived, immutable, exact-run grant that lets the canonical
organization owner authorize one named decision actor to resolve that actor's
specific requester, evidence-submitter, or evidence-linker conflict. The grant
is a delegated capability, not a generally assignable role permission.

The canonical owner must retain both `evaluation:decision` and the reserved
`evaluation:separation:override` permission in the system owner role. The named
grantee must retain `evaluation:decision` when the grant is issued and when it
is consumed. Runtime role, invitation, and membership APIs continue to reject
or strip the reserved override permission.

## Grant contract

`POST .../runs/{run_id}/separation-override-grants` accepts a named grantee,
the expected verdict version, and a bounded private reason. PostgreSQL locks
and binds the grant to the exact organization, workspace, system, run,
contract version, execution envelope identity and hash, evidence-set hash,
verdict version, grantor, grantee, and conflicting relationships. Database
time fixes a 30-minute lifetime.

The response exposes the grant identity, actors, version, and timestamps but
not the raw reason. The mutation, immutable grant, idempotency completion, and
success audit are one transaction. The audit stores only a reason hash and
the exact recomputed waived relationships.

## Consumption contract

`POST .../runs/{run_id}/separation-override-grants/{grant_id}/decision` is
available only to the named grantee. It rechecks current owner authority,
grantee membership and `evaluation:decision`, expiry, verdict version,
execution envelope, evidence set, and separation conflict under database row
locks. The immutable decision references the grant through a unique nullable
foreign key, making successful consumption single-use.

All ordinary decision invariants remain mandatory: a succeeded run, accepted
verified evidence, operational freshness, exact suite verdict coverage,
chronology, compare-and-swap versioning, idempotency, and the per-organization
audit hash chain. The override changes only the actor-separation comparison.

## Failure and release boundaries

- SQLite carries schema parity but rejects delegated grant and decision writes.
- Direct SQL grant or delegated-decision fabrication fails unless its exact
  completed idempotency and audit binding commits in the same transaction.
- The existing atomic canonical-owner decision endpoint remains unchanged.
- The master, governance-decision, and separation-override gates all remain
  default-off.
- This does not mount workers, issue worker credentials, enable automatic
  enforcement, add a frontend workflow, or constitute public rollout.

No revoke or mutable grant-status workflow is added. Revoking owner authority
or the grantee's decision permission immediately makes an unused grant
unavailable; expiry, graph drift, version drift, or prior consumption does the
same.
