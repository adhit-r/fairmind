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
