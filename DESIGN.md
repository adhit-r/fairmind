---
name: FairMind
description: A direct, evidence-led workbench for governing AI systems.
colors:
  assurance-teal: "oklch(0.60 0.13 163)"
  action-orange: "#FF6B35"
  deep-ink: "#0F1412"
  warm-canvas: "#FCFDF8"
  quiet-surface: "#F3F5F0"
  muted-text: "#59615D"
  critical-red: "#D83A2E"
typography:
  headline:
    fontFamily: "Raleway, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Raleway, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "0"
  body:
    fontFamily: "Raleway, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.5
    letterSpacing: "0"
  label:
    fontFamily: "Raleway, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.06em"
rounded:
  square: "0px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.action-orange}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "12px 16px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.warm-canvas}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.label}"
    rounded: "{rounded.square}"
    padding: "12px 16px"
    height: "44px"
  input:
    backgroundColor: "{colors.warm-canvas}"
    textColor: "{colors.deep-ink}"
    typography: "{typography.body}"
    rounded: "{rounded.square}"
    padding: "10px 12px"
    height: "44px"
---

# Design System: FairMind

## Overview

**Creative North Star: "The Assurance Workbench"**

FairMind is a shared technical workbench for engineers, compliance leads, and auditors. It is dense enough for evidence review, calm enough for sustained work, and explicit about what is observed, inferred, accepted, failed, or unknown. The product register is task-first: every screen begins with scope, decision state, blockers, and the next useful action.

The interface uses professional neobrutalism as structure rather than decoration. Square geometry, high-contrast borders, and hard shadows establish hierarchy. Teal identifies assurance context, orange identifies deliberate action, and semantic colors communicate state. Marketing hero layouts, generic AI visuals, purple gradients, glass effects, and decorative card walls are prohibited.

**Key Characteristics:**

- System-first navigation with a framework lens.
- Compact scope and decision context.
- Tables and split views for controls, evidence, and findings.
- Visible provenance, freshness, ownership, and review status.
- Strong borders and selective hard shadows.
- Responsive, keyboard-complete workflows.

## Colors

The palette combines restrained teal assurance context with a high-visibility orange action color and warm, tinted neutrals.

### Primary

- **Assurance Teal** (`oklch(0.60 0.13 163)`): active governance context, selected navigation, framework identity, and informational status.

### Secondary

- **Action Orange** (`#FF6B35`): primary actions, active task emphasis, and deliberate hover feedback. It is never a decorative page wash.

### Tertiary

- **Critical Red** (`#D83A2E`): failed controls, destructive actions, expired evidence, and critical findings.

### Neutral

- **Deep Ink** (`#0F1412`): primary text, strong borders, and active navigation.
- **Warm Canvas** (`#FCFDF8`): main application background and report surface.
- **Quiet Surface** (`#F3F5F0`): toolbars, secondary panels, table headers, and disabled context.
- **Muted Text** (`#59615D`): supporting labels and timestamps that still meet contrast requirements.

**The Evidence Color Rule.** Color may reinforce a labelled state, but color alone never carries readiness, severity, freshness, or review meaning.

**The Orange Action Rule.** Orange identifies an action or active task. If orange covers an entire dashboard region, it has been overused.

## Typography

**Display Font:** Raleway with system-ui fallback

**Body Font:** Raleway with system-ui fallback

**Label Font:** Raleway with system-ui fallback

**Character:** One direct sans family keeps technical data, controls, and decisions coherent. Hierarchy comes from weight, size, spacing, and placement instead of display typography.

### Hierarchy

- **Headline** (800, 1.5rem, 1.15): page and major section headings.
- **Title** (700, 1rem, 1.25): control names, evidence titles, and panel headings.
- **Body** (500, 0.875rem, 1.5): descriptions, guidance, findings, and review rationale. Long prose is limited to 70ch.
- **Label** (800, 0.75rem, 0.06em, uppercase): compact metadata and action labels. It must not replace readable sentence case for long text.

**The Scan First Rule.** A reviewer must identify scope, status, owner, and next action without reading paragraph text.

## Elevation

Elevation is structural and sparse. Most surfaces are separated by borders, spacing, and background tone. Hard shadows indicate an interactive primary surface, active navigation, or a raised work panel. Nested shadows are prohibited.

### Shadow Vocabulary

- **Action Lift** (`6px 6px 0 0 #0F1412`): primary buttons and a small number of interactive work surfaces.
- **Panel Lift** (`8px 8px 0 0 #0F1412`): one dominant panel when visual separation is necessary.
- **Pressed State** (`0 0 0 0 #0F1412` with translated position): direct feedback for button activation.

**The Flat By Default Rule.** Tables, toolbars, filters, and nested content remain flat. A shadow must explain interaction or hierarchy.

## Components

### Buttons

- **Shape:** square corners (`0px`) with a strong `2px` border and at least `44px` height.
- **Primary:** Action Orange background, Deep Ink text, bold label, and Action Lift shadow.
- **Hover / Focus:** move to the shadow position over 150 to 200ms; preserve a visible 2px focus ring and reduced-motion behavior.
- **Secondary:** Warm Canvas background with the same border and size vocabulary.
- **Destructive:** Critical Red background with explicit destructive copy. Never rely on an icon alone.

### Chips

- **Style:** square, compact, bordered labels for filters and state.
- **State:** selected chips use Deep Ink or Assurance Teal with readable text; unselected chips remain flat on Quiet Surface.

### Cards / Containers

- **Corner Style:** square (`0px`).
- **Background:** Warm Canvas or Quiet Surface.
- **Shadow Strategy:** flat by default; one raised panel per task region at most.
- **Border:** `2px` for normal grouping and `4px` only for dominant module boundaries.
- **Internal Padding:** 16px compact, 24px standard, 32px only for empty states.

Cards are not the default layout primitive. Use tables, split views, grouped rows, and section boundaries for governance data.

### Inputs / Fields

- **Style:** Warm Canvas, `2px` Deep Ink border, square corners, persistent label.
- **Focus:** visible teal or ink ring without layout shift.
- **Error / Disabled:** labelled semantic state with supporting text; disabled controls retain readable contrast.

### Navigation

The existing collapsible left sidebar remains. AI Governance is one expanded category with six destinations. Active items use Deep Ink with Action Orange emphasis. A compact company and AI-system scope strip sits above module content. Mobile navigation uses the existing sheet behavior and keeps task labels visible.

### Control Trace Row

A control trace row presents framework ID, shared control, assessment state, owner, evidence count, latest evaluation, freshness, and findings in one scan line. Expanding the row reveals mapping rationale and the chronological evidence trail without opening a modal.

### Framed Functional Icons

Framed icons identify navigation and direct actions. The anatomy is a square Deep Ink border, Warm Canvas or semantic fill, one high-contrast line icon, and a short hard offset shadow. Compact controls are exactly 44px or larger; expanded controls pair the same icon frame with a visible task label. Hover and pressed states move the control toward the shadow rather than adding glow or blur.

Every icon-only button or link has a specific accessible name. The icon itself is hidden from assistive technology so the control is announced once. Use the frame for navigation, refresh, open, menu, profile, and other functional controls. Do not frame decorative illustrations, table status glyphs, verdict marks, or every inline metadata icon.

### Illustrated Identity

The profile identity uses the approved illustrated portrait inside a square bordered frame. Expanded navigation shows portrait, name, and supporting account text; collapsed and header treatments retain a labelled 44px portrait control. The portrait is self-hosted at `/profile-portrait.svg` through `FramedIdentity`; authenticated screens must not request an avatar from a third-party UI host. Keep the asset path centralized and retain the same crop and frame.

Image failure is a designed state. Failed or already-broken portrait loads switch to labelled two-letter initials on Action Orange, including failures that occur before client hydration. The initials fallback keeps the same dimensions, accessible name, border, focus treatment, and interaction target.

### Evaluation State Semantics

Evaluation runs always expose three independent axes. They are rendered as labelled rows or columns, never collapsed into one score or one traffic-light color:

- **Execution status:** `queued`, `running`, `awaiting_evidence`, `succeeded`, `failed`, `timed_out`, or `cancelled`. It describes whether the evaluator completed its work.
- **Evaluator evidence result:** `pending`, `passed`, `passed_with_limitations`, `failed`, `informational`, `error`, `unavailable`, `insufficient_data`, or `unknown`. It describes what the evaluator found, including a failed model result from a successfully completed evaluator.
- **Governance verdict:** `approved`, `conditional`, `review`, `blocked`, or `insufficient`. It describes the current human-governed decision supported by admitted evidence.

`succeeded` never implies `passed`, and neither implies `approved`. `awaiting_evidence`, `unavailable`, `insufficient_data`, and `insufficient` remain neutral, explicit states rather than being presented as success or failure. `review` uses Action Orange to signal required human attention, not a passed result. Component-layer verdicts and risk-dimension verdicts remain separate labelled sections; an absent axis reads “Not assessed.”

### Evidence Admission And Trust Panel

Every evidence detail view shows the exact scope before the result: organization, workspace, AI system, target version and digest, plan hash, suite version and digest, suite execution, lifecycle phase, execution depth, delivery source, evaluator identity and adapter version, and envelope/passport identifiers. Scope is part of the query key; when any scope identity changes, the prior panel clears before the next response is shown. Responses whose organization, system, plan, run, suite execution, target, or envelope does not match the requested scope are rejected and rendered as a bounded error.

The trust panel keeps these states visible beside the three result axes:

- **Admission:** `pending`, `verified`, `unverified`, `expired`, `superseded`, `rejected`, or `trust_error`.
- **Review:** `pending`, `accepted`, or `rejected`.
- **Freshness:** `current`, `expiring`, `stale`, or `superseded`.
- **Provenance:** signer, issuer, signing-key identifier, source (`fairmind_worker`, `external_provider`, or `imported_report`), verification time, expiry, and invalidation reason.

Imported or unsigned reports remain visibly `unverified` and human-review-only. Linking a Passport can produce `review` or `insufficient`; it never directly produces `approved` or `blocked`. A reviewer outcome changes the review axis only. It must not rewrite technical status, evaluator evidence result, run outcome, or governance verdict.

### Worker Security Envelope

The UI may expose a worker attempt only through its server-generated Execution Envelope. The envelope contains immutable target and suite bindings, configuration and plan hashes, phase/depth/delivery, nonce, runner-image digest, budgets, input bindings, and trust-policy version. It excludes credentials, raw secrets, unrestricted model weights, private reasoning traces, and host paths. Artifact references are immutable SHA-256 content-addressed identifiers resolved through short-lived brokers. A worker result is not decision-grade until its signed Passport matches the envelope, suite execution, target digest, nonce, and current trust policy.

### Evaluation Runs Workbench

Evaluation Runs is one dense, flat work surface inside the established dashboard shell. Its scan order is title and assurance purpose, layout-owned organization and real AI-system context, plan selection or compact creation form, preflight blocker and next action, then the recent-runs table. Synthetic fallback systems are never displayed as real scope and never trigger evaluation requests.

The plan form keeps target kind, lifecycle phases, depth, enforcement, delivery, and immutable suite versions visible together. Preflight states state both whether a run can be prepared and whether FairMind execution is available. External and imported plans may prepare an `awaiting_evidence` run, but the interface continues to state that an exact Evidence Passport revision is required.

The recent-runs table keeps technical status and overall verdict in separate columns. Run details show plan metadata, only the layer results supplied by the evidence, exact evidence-run and Passport-revision identifiers, and an “Awaiting evidence” state when no revision is linked. It never fabricates artifacts, scores, layer findings, or compliance claims.

### Interaction Accessibility

- Meet WCAG 2.2 AA contrast for text, controls, status fills, and focus indicators.
- Keep every actionable control at least 44px by 44px on desktop and touch layouts.
- Give icon-only controls precise accessible names and keep expanded task labels visible.
- Preserve a visible 2px keyboard focus outline with offset on every link, button, field, and menu trigger.
- Keep semantic headings, fieldsets, tables, status regions, and alerts so loading, empty, server-error, and action-error states are distinguishable without color.
- Under `prefers-reduced-motion: reduce`, remove translations, animated skeleton pulses, and non-essential transitions while preserving immediate state feedback.
- Preserve the white, Deep Ink, teal, orange, square-border, hard-shadow language. Purple gradients, generic AI styling, glass effects, glow, and decorative dashboard metrics remain prohibited.

## Do's and Don'ts

### Do:

- **Do** show company, AI system, framework version, and review period before readiness information.
- **Do** use shared controls and reviewed evidence links across frameworks.
- **Do** pair every status color with a text label and accessible name.
- **Do** use tables and split views for dense governance work.
- **Do** preserve the established teal, orange, Deep Ink, and Warm Canvas language.
- **Do** provide loading skeletons, instructive empty states, error recovery, keyboard navigation, and responsive overflow.

### Don't:

- **Don't** use purple gradients, gradient text, glassmorphism, neon glow, or generic AI product styling.
- **Don't** place marketing heroes inside the authenticated dashboard.
- **Don't** create identical card grids or nested cards for control and evidence lists.
- **Don't** use a colored side-stripe border as an accent.
- **Don't** imply that a score, accepted artifact, or FairMind evaluation automatically proves compliance or certification.
- **Don't** introduce a different component vocabulary for AIUC-1.
- **Don't** store raw model weights, unrestricted prompts, or private reasoning traces by default.
