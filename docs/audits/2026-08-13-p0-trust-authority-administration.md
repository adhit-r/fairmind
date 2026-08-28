# P0 trust-authority administration evidence

Date: 2026-08-13

## Scope

This checkpoint adds a default-off administration boundary for evidence
issuers, public Ed25519 verification keys, and immutable trust-policy versions.
It also hardens legacy role delegation so the trust-root permission cannot be
self-issued through the organization-management API.

This is an internal control-plane capability. It is not worker execution,
automatic enforcement, certification, or production-readiness evidence.

## Implemented controls

- Trust mutations require both the Assurance V2 master flag and the independent
  trust-administration flag. Every directly mountable trust router enforces both
  flags before authentication, request parsing, or service execution.
- Authorization uses the literal persisted `evaluation:trust:admin` permission.
  Organization role names, token claims, wildcard permissions, and undeclared
  aliases do not grant trust authority.
- Legacy role creation, assignment, invitation, acceptance, update, and
  reactivation cannot delegate trust administration, worker authority, or a
  separation-of-duty override. Malformed stored permission containers authorize
  nothing.
- Mutations require an `Idempotency-Key`, use the existing organization-scoped
  audited transaction boundary, and are PostgreSQL-only. SQLite remains a
  read/parity fixture and fails closed before a trust mutation.
- Signing keys accept only canonical, public-only Ed25519 JWKs. FairMind derives
  the algorithm and public-key fingerprint and never accepts private key
  material.
- Trust-policy documents are closed and server-hashed. Policies are born in
  draft, activated with exact compare-and-swap expectations, progress through
  attributed one-way lifecycle transitions, and cannot relax the predecessor's
  bounded controls.
- Issuer and key revocation require attributed, bounded rationales. Policy
  replacement atomically retires the active predecessor; an explicitly bounded
  recovery path can activate the declared successor of the latest retired
  predecessor without creating two active policies.
- Migration 013f adds database constraints, triggers, lifecycle attribution,
  policy lineage, global key-fingerprint uniqueness, canonical key and policy
  validation, one-active-policy enforcement, and checksum/catalog drift
  detection without rewriting migrations 013 through 013e.

## Verification evidence

- Trust service, repository, route, role-delegation, and migration slices passed
  focused unit and integration tests.
- A disposable PostgreSQL 14.18 instance passed the native 013f behavior,
  replay, operator-chain, catalog-freeze, and tamper checks.
- An independent PostgreSQL race harness passed 14 of 14 scenarios, including
  concurrent first and successor activation, both retire-versus-activate
  orderings, emergency recovery, issuer and signing-key revocation, stale CAS,
  cross-tenant access, and global fingerprint races. Every race produced one
  authoritative winner and a fail-closed loser.
- The route inventory covers all 13 trust endpoints and verifies that literal
  trust-admin authority is required before service entry.
- Backend layer-boundary, no-archive-import, compilation, and diff-integrity
  checks passed for the reviewed snapshot.

## Known boundary

The PostgreSQL evidence is local and disposable; it is not staging or production
proof. At this checkpoint the master issuer/key/policy/admission/freshness/review
row remained open because operational freshness had no database-authoritative
read projection. Migration 013g closes that later checkpoint; see
`2026-08-13-p0-operational-evidence-freshness.md`. Service-worker identity,
audited separation-of-duty overrides, worker execution, runtime enforcement,
and the private governance pilot remain open.
