---
name: FairMind
description: A calm, precise, evidence-led workbench for governing AI systems.
colors:
  fm-bg: "#f4f4f2"
  fm-ink: "#15171a"
  fm-ink2: "#5a5f68"
  fm-ink3: "#6a707c"
  fm-line: "rgba(21, 23, 26, 0.08)"
  fm-brand: "#ff6b35"
  surface: "#ffffff"
  identity-tile: "#2b2e3a"
  status-done-text: "#00704e"
  status-done-fill: "#e3f5ec"
  status-block-text: "#b42318"
  status-block-fill: "#fde8e8"
  status-warn-text: "#8a5a00"
  status-warn-fill: "#fff4d6"
  status-info-text: "#1d4f91"
  status-info-fill: "#e6effb"
  status-attention-text: "#a8430b"
  status-attention-fill: "#ffeee4"
  destructive: "#b4232c"
shadows:
  fm-shadow: "0 1px 2px rgba(20, 20, 30, 0.04), 0 18px 44px -20px rgba(20, 20, 30, 0.22)"
typography:
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "0"
  control:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0"
  control-secondary:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0"
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.65625rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
    textTransform: "uppercase"
rounded:
  card: "14px"
  control: "10px"
  identity-org: "7px"
  pill: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.fm-ink}"
    textColor: "{colors.surface}"
    typography: "{typography.control}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fm-ink2}"
    border: "1px solid {colors.fm-line}"
    typography: "{typography.control-secondary}"
    rounded: "{rounded.pill}"
    padding: "0 16px"
    height: "40px"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fm-ink}"
    rounded: "{rounded.card}"
    shadow: "{shadows.fm-shadow}"
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.fm-ink}"
    border: "1px solid {colors.fm-line}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    height: "40px"
  pill:
    backgroundColor: "{colors.fm-bg}"
    textColor: "{colors.fm-ink2}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
---

# Design System: FairMind

## Overview

**Creative North Star: "The Assurance Workbench"**

FairMind is a shared technical workbench for engineers, compliance leads, and auditors. It is calm, precise, and trustworthy: quiet surfaces, clear hierarchy, and data that reads at a glance. It is explicit about what is observed, inferred, accepted, failed, or unknown. Every screen begins with scope, decision state, blockers, and the next useful action.

The visual language is the **lifecycle shell**. The reference pages are `/dashboard`, `/integrations`, `/onboard`, and `/systems/[id]`, all rendered inside `AppShell` (`apps/frontend/src/components/layout/AppShell.tsx`). Tokens live in `apps/frontend/src/app/globals.css`; shared primitives live in `apps/frontend/src/components/ui/` (Card, Button, dropdown, FramedIcon) and `apps/frontend/src/components/packs/parts.tsx` (Pill, `BTN`, `BTN_P`, `LABEL`, `LINE`).

**Retired: the neobrutalist style.** The earlier "professional neobrutalism" language is retired and must not be reintroduced: the `#0F1412` / `#FCFDF8` / `#F3F5F0` palette, hard offset shadows (`6px 6px 0 0`, `8px 8px 0 0`, `shadow-brutal*`), `border-2` / `border-4 border-black`, square `rounded-none` geometry, `font-black uppercase` labels, press-down translate transforms, and orange fill buttons. The Raleway type family went with it.

**Key Characteristics:**

- White cards with 14px corners and a soft layered shadow on a warm grey page.
- Hairline 1px borders in `--fm-line`, never heavy outlines.
- Ink, not black: `--fm-ink`, `--fm-ink2`, `--fm-ink3` carry text and primary fills.
- Semibold type with tight tracking; uppercase only on 10-11px section labels.
- Rounded-full pill controls; the primary control is a dark ink pill.
- Orange (`--fm-brand`) is a brand accent for marks and highlights, not a button color.
- No gradients, gloss, glow, hard offset shadows, or press-down transforms.

## Colors

All neutrals are referenced through `var(--fm-*)`; hex values for ink, lines, and backgrounds are never hardcoded in components. Status colors are the only literals.

### Neutral (shell tokens, `globals.css`)

- **Page** `--fm-bg` (`#f4f4f2`): the warm grey page background and quiet fills (secondary buttons, plain pills, icon chips).
- **Ink** `--fm-ink` (`#15171a`): primary text, primary pill fill, active navigation fill, focus ring.
- **Ink 2** `--fm-ink2` (`#5a5f68`): secondary text, secondary button text, supporting metadata.
- **Ink 3** `--fm-ink3` (`#6a707c`): section labels, timestamps, tertiary actions. The value in `globals.css` is authoritative; older notes listing `#9096a0` are superseded by the darker, higher-contrast value.
- **Line** `--fm-line` (`rgba(21,23,26,.08)`): every hairline border and row divider.
- **Surface** (`#ffffff`): cards, inputs, secondary buttons.

### Brand accent

- **Brand** `--fm-brand` (`#ff6b35`): the FairMind mark, the active lifecycle station on the spine, and small highlights. It is never a button fill, never a status-chip fill, and never a page wash. Verdicts that need a person (such as `review`) use the attention status pair, not the brand accent.

### Status

Status colors pair a tinted fill with a darker text color (Pill tones in `packs/parts.tsx`): done `#00704e` on `#e3f5ec`, blocked `#b42318` on `#fde8e8`, warning `#8a5a00` on `#fff4d6`, info `#1d4f91` on `#e6effb`, attention (needs you) `#a8430b` on `#ffeee4`. The destructive button uses `#b4232c`.

The shadcn `--primary` / `--accent` variables still hold a teal value for third-party primitives; lifecycle-shell pages do not use teal as an identity or action color.

**The Evidence Color Rule.** Color may reinforce a labelled state, but color alone never carries readiness, severity, freshness, or review meaning.

## Typography

**Family:** Inter, loaded through `next/font` as `--font-inter` and exposed as Tailwind `font-sans`. Body text enables `cv11`, `ss01`, and tabular numerals (`tnum`).

### Hierarchy

- **Headline** (600, 28-34px, 1.1, -0.03em tracking): page headings (`/dashboard` uses 30px, 34px from `lg`).
- **Title** (600, about 15px, slight negative tracking): card and panel headings, the wordmark.
- **Body** (400-500, 13-13.5px, 1.5): descriptions, findings, and rationale. Long prose is limited to 70ch.
- **Control** (600, 13px): button and navigation text; 12.5px on small buttons.
- **Label** (600, 10.5px, 0.08em, uppercase, `--fm-ink3`): section labels (`.fm-sec`, `LABEL`). Uppercase is used only at this size.

**The Scan First Rule.** A reviewer must identify scope, status, owner, and next action without reading paragraph text.

## Elevation

One shadow, `--fm-shadow` (`0 1px 2px rgba(20,20,30,.04), 0 18px 44px -20px rgba(20,20,30,.22)`), lifts cards off the page (`.fm-card`, `Card`). The org block uses only its first, 1px layer. Everything inside a card is flat: tables, toolbars, filters, and rows are separated by `--fm-line` hairlines and spacing. Nested shadows, hard offset shadows, and glow are prohibited.

## Components

### Buttons

`Button` (`components/ui/button.tsx`) and the `BTN` / `BTN_P` class strings are the only button vocabularies.

- **Shape:** `rounded-full`, 40px high (`h-10`) by default, 36px small, 44px large.
- **Primary:** `--fm-ink` fill, white 13px semibold text, hover to black. No shadow, no transform.
- **Secondary:** white with a `--fm-line` hairline and `--fm-ink2` text at medium weight (500); hover darkens the border and text to ink. `Button` `neutral` / `outline` is the canonical secondary.
- **Quiet:** `--fm-bg` fill with ink text.
- **Destructive:** `#b4232c` fill with explicit destructive copy. Never rely on an icon alone.
- **Focus:** 2px `--fm-ink` ring with 2px offset. Disabled controls drop to 60% opacity and keep their label.
- **Known divergence:** the `BTN` class string still uses semibold `--fm-ink` text and 50% disabled opacity. Prefer `Button`; migrate `BTN` to the values above.

### Pills

`Pill` (`packs/parts.tsx`) is the state chip: `rounded-full`, 11.5px semibold, tinted fill per tone, optional leading dot. Filters and status labels use pills; they are flat and borderless.

### Cards / Containers

- **Corner:** 14px.
- **Background:** white on the `--fm-bg` page.
- **Shadow:** `--fm-shadow`; never stacked.
- **Border:** none on cards; 1px `--fm-line` for inner dividers and bordered rows.
- **Padding:** 16px compact, 24px standard, 32px only for empty states.

Cards group a task region. Inside a card, use tables, split views, grouped rows, and hairline dividers for governance data rather than nested cards.

### Inputs / Fields

White, 1px `--fm-line` border, `rounded-[10px]`, persistent visible label. Focus shows the ink ring without layout shift. Errors carry a labelled message; disabled fields keep readable contrast.

### Navigation

`AppShell` draws a 236px sidebar on the `--fm-bg` page: the FairMind mark, the organisation block, a dark ink pill for the current home link, then the lifecycle **spine**: a 2px `--fm-line` rail with one station per lifecycle stage, each carrying its live count. The station that needs attention is marked with `--fm-brand`. Below 768px the spine becomes a horizontally scrolling strip (`.fm-strip`). Active items use the ink fill with white text.

### Control Trace Row

A control trace row presents framework ID, shared control, assessment state, owner, evidence count, latest evaluation, freshness, and findings in one scan line, separated from its neighbours by a hairline. Expanding the row reveals mapping rationale and the chronological evidence trail without opening a modal.

## Identity And Icons

### Brand mark

The mark is a 22px `--fm-brand` square with 8px corners (`rounded-md`, `--radius` minus 2px) next to the "FairMind" wordmark (15px, bold, tight tracking). It links to `/dashboard`. The brand orange appears here, on spine highlights, and on the small highlights listed under Colors; never as a fill for status or verdict chips.

### Organisation and person identity

Identity is local and initials-based. No portrait image and no third-party avatar host is requested by authenticated screens; the earlier illustrated portrait (`/profile-portrait.svg`, `FramedIdentity`) is retired from the shell.

- **Organisation:** a 26px tile with 7px corners in `#2b2e3a`, white 11px semibold initials, beside the organisation name and role. With several organisations the name becomes a labelled `select` ("Organisation").
- **Person:** a 32px round `#2b2e3a` tile with initials, the username or email, the role, and a quiet "Sign out" text action. It reads the one verified session (`useSession`).
- **Initials:** the first letters of the first two words of the name, split on spaces, `@`, `.`, `_`, and `-`, uppercased (`initials()` in `AppShell`).

### Functional icons

`FramedIcon` (`components/ui/FramedIcon.tsx`) is the icon control. It accepts Tabler icons (`@tabler/icons-react`); new controls use Tabler.

- **Compact (icon-only):** a 40px round white control with a `--fm-line` hairline; hover darkens the border to ink. 20px icon.
- **Expanded (with label):** a full-width `rounded-[10px]` row; the 16px icon sits in a 32px round `--fm-bg` chip beside a 13.5px label and an optional trailing slot. Hover fills the row with `--fm-bg`.
- **Active:** `--fm-ink` fill with white text; the icon chip becomes translucent white.
- **Accessibility:** `label` is required and becomes the control's `aria-label`; the icon is `aria-hidden` so the control is announced once. Colour transitions only, 150ms, removed under reduced motion.

Use `FramedIcon` for navigation, refresh, open, menu, and other functional controls. Do not frame decorative illustrations, table status glyphs, verdict marks, or inline metadata icons.

## Assurance Contract V2

### Evaluation State Semantics: the three axes

Evaluation runs and suite executions always expose three independent axes (`apps/backend/src/application/evaluation_workbench_contracts.py`). They are rendered as labelled rows or columns, never collapsed into one score or one traffic-light color:

- **Execution status** (`TECHNICAL_STATUSES`): `awaiting_evidence`, `queued`, `leased`, `running`, `succeeded`, `failed`, `timed_out`, or `cancelled`. It describes whether the evaluator completed its work. `succeeded`, `failed`, `timed_out`, and `cancelled` are terminal.
- **Evaluator evidence result** (`EVIDENCE_RESULTS`): `pending`, `passed`, `passed_with_limitations`, `failed`, `informational`, `error`, `unavailable`, `insufficient_data`, or `unknown`. It describes what the evaluator found, including a failed model result from a successfully completed evaluator. `EVIDENCE_RESULTS_BY_TECHNICAL_STATUS` constrains the pairing: a non-terminal status carries only `pending`. A Passport reporting `passed_with_limitations` must name at least one limitation.
- **Governance verdict** (`GOVERNANCE_VERDICTS`): `approved`, `conditional`, `review`, `blocked`, or `insufficient`. It describes the current human-governed decision supported by admitted evidence. A new run starts at `insufficient` with every suite layer `insufficient`; a run with `verdict_version` 0 may carry only `review` or `insufficient`.

`succeeded` never implies `passed`, and neither implies `approved`. `awaiting_evidence`, `unavailable`, `insufficient_data`, and `insufficient` remain neutral, explicit states rather than success or failure. `review` uses the attention Pill tone (`#a8430b` on `#ffeee4`, tone `you` in `packs/parts.tsx`) to signal required human attention, not a passed result. The orange `bg-[#FF6B35]` Review chip in `components/evaluations/EvidenceTrustPanel.tsx` (bordered, uppercase) is legacy styling to migrate to that tone. Layer verdicts (`suites`, `modalities`, `components`, `riskDimensions`) stay separate labelled sections; an absent axis reads "Not assessed."

### Evidence Admission And Trust Panel

These are the v2 trust-panel and API contract rules. A legacy response that does not carry a field renders `Not returned by this response` or `Not assessed`; it is never upgraded into a stronger claim by the client.

Every evidence detail view shows the exact scope before the result: organization, workspace, AI system, target version and digest, plan hash, suite version and digest, suite execution, lifecycle phase, execution depth, delivery source, evaluator identity and adapter version, and envelope/passport identifiers. Scope is part of the query key; when any scope identity changes, the prior panel clears before the next response is shown. Responses whose organization, system, plan, run, suite execution, target, or envelope does not match the requested scope are rejected and rendered as a bounded error.

The v2 preview route is `/assurance/evaluations/:runId`. Its request boundary requires both frontend gates, `NEXT_PUBLIC_ASSURANCE_V2_UI_ENABLED` and `NEXT_PUBLIC_ASSURANCE_V2_RUN_UI_ENABLED`; when either is off, the UI renders an explicit disabled state and makes no v2 run request. The API independently requires both backend gates, `assurance_v2_enabled` and `assurance_v2_runs_enabled`. The canonical app does not mount the run routes when either backend gate is off; direct or compatibility-router mounting also enforces a stable feature-disabled guard before endpoint authentication, request-body parsing, database access, or service composition. The client keeps any server rejection bounded as denied or unavailable, and no gate state falls back to v1 or fixture evidence.

The trust panel keeps these states visible beside the three result axes:

- **Admission** (`ADMISSION_STATUSES`): `pending`, `verified`, `unverified`, `expired`, `superseded`, `rejected`, or `trust_error`.
- **Review** (`REVIEW_STATUSES`): `pending`, `accepted`, or `rejected`.
- **Freshness** (`FRESHNESS_STATUSES`): `current`, `expiring`, `stale`, or `superseded`.
- **Provenance:** signer, issuer, signing-key identifier, source (`fairmind_worker`, `external_provider`, or `imported_report`), verification time, expiry, and invalidation reason.

Imported or unsigned reports remain visibly `unverified` and human-review-only: a signed Passport V2 can never carry the `imported_report` delivery mode. Linking a Passport can produce `review` or `insufficient`; it never directly produces `approved` or `blocked`. A reviewer outcome changes the review axis only. It must not rewrite technical status, evaluator evidence result, run outcome, or governance verdict.

### Binding Model

Decision-grade evidence is one chain of hashes from the target under test to the signed Passport. Every hash is SHA-256 over RFC 8785 canonical JSON inside the I-JSON domain (`canonical_json_bytes` / `canonical_sha256` in `src/domain/assurance/evaluation_v2.py`). The server owns every link in the chain; the client never computes or repairs one.

**1. Versioned inputs (migration 013, immutability in 013a).** Three versioned records feed a plan, and their bindings cannot change once written:

- **Target version** (`governance_evaluation_target_versions`): target key and kind, system version, subject kind/id/version, the **target version digest** (`subjectDigest`), deployment and connector binding, and the manifest digest. Status `active`, `superseded`, or `retired`.
- **Suite version** (`governance_evaluation_suite_versions`): suite ref, owner scope, manifest digest, worker type, runner image digest (`sha256:` OCI form), adapter name and version, result contract version, required input roles, and budgets.
- **Trust policy version** (`governance_evidence_trust_policy_versions`): id, version, and `policyHash`, plus the maximum evidence age and the unsigned-import policy (`reject` or `manual_review`).

**2. Plan / configuration hash.** `plan_content_projection` (`evaluation_v2.py`) projects organization, workspace, system, the full target binding, lifecycle phases, execution depth, enforcement mode, delivery mode, the trust policy (`id`, `version`, `policyHash`), and each selected suite (`ordinal`, `suiteVersionId`, `ownerScope`, `suiteRef`, `manifestDigest`, `configuration`, `configurationHash`). `EvaluationPlanService` stores its hash as `plan_content_hash`. Each suite's selected configuration has its own `configurationHash`, so changing one configuration value changes the plan hash. Plan bindings are immutable (013a); a change means a new plan.

**3. Execution envelope and nonce.** `EvaluationRunService` builds one `ExecutionEnvelopeV2` per run with `build_execution_envelope_v2`, after preflight passes. It mints the run id, envelope id, one **suite execution** id per selected suite, and a **nonce** of 32 random bytes encoded as 43-character unpadded base64url. The envelope carries `schemaVersion`, `envelopeId`, `runId`, organization/workspace/system, `planId`, `planContentHash`, the target binding (including `subjectDigest`), trigger, lifecycle phase, depth, enforcement, delivery, the trust policy binding, the nonce, `requesterId`, `requestedAt` (canonical UTC), and one suite binding per suite execution (suite version, manifest digest, worker type, runner image digest, adapter, result contract, configuration and `configurationHash`, input roles, budgets, and the target manifest's content-addressed input descriptors). The **execution envelope hash** is SHA-256 over its canonical bytes, capped at 512 KiB. The run row stores `envelope_json`, `envelope_hash`, and `envelope_nonce` separately; 013a requires the nonce inside the JSON to equal the column, makes run bindings immutable, and enforces `UNIQUE (org_id, envelope_nonce)`.

**4. Evidence Passport V2.** `src/domain/assurance/evidence_passport_v2.py` defines a closed Passport whose `executionBinding` must equal, field for field, what `expected_execution_binding_v2` derives from the stored envelope for one suite execution: organization, workspace, system, `runId`, `envelopeId`, `envelopeHash`, `nonce`, `planId`, `planContentHash`, target (`targetVersionId`, `subjectDigest`, `manifestDigest`), suite (`suiteExecutionId`, `suiteVersionId`, `manifestDigest`, `configurationHash`), lifecycle phase, depth, enforcement, delivery, and trust policy (`trustPolicyVersionId`, `policyHash`). The derivation first rebuilds the envelope and rejects it if the rebuild differs from what is stored. The Passport's `contentHash` covers everything except `contentHash` and `signature`; the Ed25519 signature covers a domain-separated projection (`fairmind/evidence-signature/2.0.0`) of the content hash, algorithm, issuer, key id, and `signedAt`. The evaluator `sourceType` must equal the delivery mode, the signature issuer must equal the evaluator issuer, and the claim boundary is `supporting_evidence_only`.

**5. Admission (submit).** `VerifiedEvidenceAdmissionService` with `TrustedEvidenceAdmissionResolver` and `EvidenceAuthenticityService` admits one Passport for one suite execution in one transaction. The resolver locks the authority and checks scope; that the plan, target, trust policy, and every suite are `active`; that the issuer is active, its type equals the plan's delivery mode, and it is `fairmind_worker` or `external_provider`; issuer source/suite/target restrictions; and that the Ed25519 signing key is valid and unrevoked at database time. Authenticity then checks the content hash, issuer and key against the trusted key, the signature, tenant identity, and exact `executionBinding` equality. The authority is resolved twice and its hash must not change in between; the evaluator must match an approved registration (013d). Chronology must hold `requestedAt <= capturedAt <= signedAt <= verifiedAt`, and the effective expiry is the earliest of the Passport's `expiresAt`, `capturedAt` plus the policy's maximum evidence age, and the key's `validUntil`. The service writes the evidence run, Passport revision, verification receipt (013c, which binds the receipt's nonce to the run's `envelope_nonce`), admission, and a **nonce claim** (013b `governance_evidence_nonce_claims`, `UNIQUE (suite_execution_id, envelope_id, envelope_nonce)`, with foreign keys to both the run's `(envelope_id, envelope_hash, envelope_nonce)` and the admission). Submission does not link the evidence to the run.

**6. Link.** `VerifiedEvidenceLinkService` links an admitted Passport as a separate step. It requires admission `verified`, freshness `current`, and a link time before the effective expiry. Migration 013k re-checks the exact current authority chain in PostgreSQL at link time: active trust policy, active unrevoked issuer, unrevoked signing key inside its validity window, and an approved evaluator registration. A linked suite execution reads admission `verified`, review `pending`, freshness `current`.

**7. Freshness after link (013g).** Linked evidence degrades with a frozen set of reason codes: `recorded_superseded`, `trust_policy_superseded`, `recorded_stale`, `effective_expiry_reached`, `issuer_revoked`, `signing_key_revoked`, `signing_key_validity_ended`, `trust_policy_retired`, `evaluator_registration_revoked`, and `evidence_expiring`.

#### What breaks the binding

| Change | Where it fails | Result |
| --- | --- | --- |
| Any Passport content byte after hashing | `normalize_evidence_passport_v2` (`content_hash_mismatch`) | `evidence_passport_invalid` |
| Signature issuer differs from the evaluator issuer | `normalize_evidence_passport_v2` (`signature_issuer_mismatch`), during `parse_evidence_passport_v2` | `evidence_passport_invalid` |
| Signature value, algorithm, or key id does not verify against the resolved trusted key | `EvidenceAuthenticityService` | `evidence_authenticity_failed` |
| Different target version or `subjectDigest`, suite version, configuration, plan hash, envelope hash, nonce, or trust policy hash in `executionBinding` | exact binding equality in `EvidenceAuthenticityService` | `evidence_authenticity_failed` |
| Stored envelope no longer rebuilds to itself | `expected_execution_binding_v2` | `evidence_admission_authority_invalid` |
| A new target version, suite configuration, or trust policy | immutable bindings (013a) | needs a new plan and run; old evidence cannot bind to it |
| Plan, target, trust policy, or suite not `active` | resolver | `evidence_admission_authority_inactive` |
| Issuer unknown, inactive, wrong source type, or restricted | resolver | `evidence_issuer_untrusted` or `evidence_issuer_restricted` |
| Signing key unknown, untrusted, revoked, or outside its validity window | resolver | `evidence_signing_key_untrusted` |
| Authority changes during verification | `_verify_stable_authority` | `evidence_admission_authority_changed` |
| Out-of-order timestamps | admission chronology | `evidence_chronology_invalid` |
| Effective expiry reached | admission or link | `evidence_expired` or `verified_evidence_link_ineligible` |
| Second Passport for the same suite execution, or nonce replay | occupied check and nonce-claim uniqueness (013b) | `evidence_admission_occupied` or a constraint violation |
| Nonce reused across runs in an organization | `UNIQUE (org_id, envelope_nonce)` (013a) | run creation fails |
| Imported report presented as a signed Passport | `normalize_evidence_passport_v2` | rejected; imported evidence stays `unverified` |
| Revocation, supersession, or retirement after link | freshness (013g) | `stale` / `superseded` with a reason code |

### Capability Truth Table

The capability states below are a release policy for dashboard labels, documentation, website copy, and sales claims. Main has no runtime capability registry that enforces them; the stored v1 Passport field `capabilityState` (`validated`, `metadata_only`, `external_provider`, `unavailable`, `insufficient_data` in `evidence_passport.py`) describes one evaluation, not a product capability. A visible screen or an imported fixture is not evidence that an execution capability is available.

| Capability state | Runtime behavior | UI treatment | Permitted claim |
| --- | --- | --- | --- |
| `planned` | No route or worker is composed | Show roadmap or "Coming soon" state | Planned only |
| `experimental` | Explicitly allowlisted and independently benchmarked below a public gate | Show version, limitations, and experimental pill | Experimental evaluation support |
| `advisory` | Runs may produce supporting evidence; no automatic action | Show evidence and reviewer-needed state | Advisory evidence collection |
| `verified` | Adapter, benchmark, sandbox, red-team, and soak gates are current | Show executable capability with exact version and freshness | Named execution capability |
| `retired` | New execution is rejected; historical evidence remains readable | Show retired and invalidation/freshness state | Historical evidence only |

Current state on main: FairMind worker execution is `planned`. Preflight raises `worker_unavailable` for any plan or suite with `fairmind_worker` delivery, and `EvaluationWorkerPort` has no concrete sandbox adapter or route. External-provider and imported-report delivery are `advisory`. The product remains an internal, default-off evidence-integrity foundation; it may claim governance planning, evidence ingestion, and reviewer workflow only after their release gates, and must not claim certification, automatic compliance, automatic enforcement, or "FairMind Verified."

Automatic enforcement stays in the stored contract (`ENFORCEMENT_MODES`) so historical plans and runs remain readable, but new legacy and V2 plans cannot select it and preflight raises `automatic_enforcement_disabled`. The retired legacy API and UI environment switches do not re-enable it.

FairMind-worker delivery values also remain in the stored contract for historical and V2 compatibility, but the legacy creation boundary never exposes or accepts them. The retired switches do not re-enable worker delivery; historical worker-labelled plans stay readable while activation and run preparation remain blocked.

### Worker Security Envelope

The UI may expose a worker attempt only through its server-generated Execution Envelope (see Binding Model). The envelope contains immutable target and suite bindings, configuration and plan hashes, phase/depth/delivery, nonce, runner image digest, budgets (cases, attempts, duration, CPU, memory, processes, disk, input/output bytes, cost), content-addressed input descriptors (`kind`, `sha256`, `mediaType`, `sizeBytes`), and the trust policy binding. Envelope inputs pass `reject_sensitive_keys` and the public-safe value checks, so they exclude credentials, raw secrets, tokens and provider keys, PEM keys, JWTs, email addresses, raw prompts or outputs, private reasoning traces, and connection or `file:` URLs.

Migration 013m lays the worker foundation without composing a worker:

- **Worker identities** are per organization, with a principal subject, worker type, hashed capabilities, and status `active`, `disabled`, or `revoked` (revocation needs an actor, time, and reason).
- **Suite attempts** are numbered 1 to 3 per suite execution, with only one `leased` or `running` attempt at a time. The lease token is stored only as a SHA-256 hash, and a lease expires no more than 60 seconds after the last heartbeat. A `succeeded` attempt must reference an evidence run and Passport revision.
- **Artifacts** are content-addressed: unique per organization by SHA-256 and by storage key, at most 1 GiB, and linked to attempts by ordinal and Passport artifact id.
- **Cancellations** are recorded once per run and once per suite execution.

A worker result is not decision-grade until its signed Passport is admitted and linked under the Binding Model: matching envelope, suite execution, target digest, nonce, and current trust policy.

### Evaluation Runs Workbench

Evaluation Runs is one work surface inside the lifecycle shell. Its scan order is title and assurance purpose, layout-owned organization and real AI-system context, plan selection or compact creation form, preflight blocker and next action, then the recent-runs table. Synthetic fallback systems are never displayed as real scope and never trigger evaluation requests.

The plan form keeps target kind, lifecycle phases, depth, enforcement, delivery, and immutable suite versions visible together. Preflight states say both whether a run can be prepared and whether FairMind execution is available. External and imported plans may prepare an `awaiting_evidence` run, but the interface continues to state that an exact Evidence Passport revision is required.

The recent-runs table keeps technical status and overall verdict in separate columns. Run details show plan metadata, only the layer results supplied by the evidence, exact evidence-run and Passport-revision identifiers, and an "Awaiting evidence" state when no revision is linked. It never fabricates artifacts, scores, layer findings, or compliance claims.

## Interaction Accessibility

- Meet WCAG 2.2 AA contrast for text, controls, status fills, and focus indicators.
- Keep actionable controls at least 40px (`h-10`, `size-10`) and never below the 36px small size; use the 44px large size for primary touch actions.
- Give icon-only controls precise accessible names and keep expanded task labels visible.
- Preserve a visible 2px ink focus ring with offset on every link, button, field, and menu trigger.
- Keep semantic headings, fieldsets, tables, status regions, and alerts so loading, empty, server-error, and action-error states are distinguishable without color.
- Under `prefers-reduced-motion: reduce`, remove transitions and animated skeleton pulses while preserving immediate state feedback.

## Do's and Don'ts

### Do:

- **Do** use `var(--fm-*)` tokens and the shared Card, Button, Pill, and FramedIcon primitives.
- **Do** show company, AI system, framework version, and review period before readiness information.
- **Do** use shared controls and reviewed evidence links across frameworks.
- **Do** pair every status color with a text label and accessible name.
- **Do** use tables and split views inside cards for dense governance work.
- **Do** provide loading skeletons, instructive empty states, error recovery, keyboard navigation, and responsive overflow.

### Don't:

- **Don't** reintroduce the retired neobrutalist style: `border-2` / `border-4 border-black`, hard offset shadows, `font-black uppercase`, `rounded-none`, the `#0F1412` / `#FCFDF8` palette, or orange fill buttons.
- **Don't** use gradients, gloss, glassmorphism, neon glow, or press-down transforms.
- **Don't** hardcode hex for ink, lines, or backgrounds.
- **Don't** place marketing heroes inside the authenticated dashboard.
- **Don't** create nested cards for control and evidence lists.
- **Don't** use a colored side-stripe border as an accent.
- **Don't** imply that a score, accepted artifact, or FairMind evaluation automatically proves compliance or certification.
- **Don't** introduce a different component vocabulary for one framework.
- **Don't** store raw model weights, unrestricted prompts, or private reasoning traces by default.
