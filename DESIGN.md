---
name: FairMind Evidence Workbench
description: A forensic neobrutalist interface for producing reviewable AI assurance evidence.
colors:
  evidence-teal: "#118A72"
  signal-orange: "#FF6B35"
  assurance-ink: "#101614"
  ledger-paper: "#FBF8F1"
  quiet-surface: "#F0EEE7"
  muted-ink: "#5B665F"
  verified-green: "#17714F"
  caution-amber: "#A94E16"
  failure-red: "#B42318"
typography:
  display:
    fontFamily: "Raleway, ui-sans-serif, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 900
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Raleway, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Raleway, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 500
    lineHeight: 1.55
  label:
    fontFamily: "Raleway, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 800
    lineHeight: 1.2
    letterSpacing: "0.08em"
  data:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.8125rem"
    fontWeight: 600
    lineHeight: 1.4
rounded:
  none: "0px"
  focus: "2px"
spacing:
  1: "4px"
  2: "8px"
  3: "12px"
  4: "16px"
  6: "24px"
  8: "32px"
  12: "48px"
components:
  button-primary:
    backgroundColor: "{colors.signal-orange}"
    textColor: "{colors.assurance-ink}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
    height: "44px"
  button-secondary:
    backgroundColor: "{colors.ledger-paper}"
    textColor: "{colors.assurance-ink}"
    rounded: "{rounded.none}"
    padding: "12px 16px"
    height: "44px"
  evidence-passport:
    backgroundColor: "{colors.ledger-paper}"
    textColor: "{colors.assurance-ink}"
    rounded: "{rounded.none}"
    padding: "20px"
  status-validated:
    backgroundColor: "{colors.verified-green}"
    textColor: "{colors.ledger-paper}"
    rounded: "{rounded.none}"
    padding: "4px 8px"
---

# Design System: FairMind Evidence Workbench

## 1. Overview

**Creative North Star: "The Assurance Ledger"**

FairMind looks and behaves like a working assurance ledger: structured, tactile, and explicit about who recorded each fact. Heavy borders and hard offset shadows make important controls feel physical, while disciplined spacing and a warm paper ground keep dense governance work readable for long sessions.

This is product UI, not a campaign surface. The page should disappear into the work of running an evaluation, reviewing an evidence mapping, and preparing a decision. It explicitly rejects generic AI governance suites, generic AI tool marketing, purple gradients, neon-on-black cyber styling, glassmorphism, soft card clouds, and ornamental animation.

**Key Characteristics:**

- High-contrast light canvas designed for daytime assurance and engineering work.
- Sharp geometry, strong full borders, and hard shadows used as structural affordances.
- Teal for trustworthy system context, orange for the next action, ink for authority.
- Dense evidence details with progressive disclosure, not a wall of interchangeable cards.
- Capability state, provenance, limitations, and review status always visible.

## 2. Colors

The palette is a restrained evidence ledger with two functional signals: teal establishes trusted context, and orange marks the next consequential action.

### Primary

- **Evidence Teal:** Primary selection, organization and system context, accepted mappings, and active navigation.

### Secondary

- **Signal Orange:** Primary actions, pending review, active filters, and moments requiring a decision.

### Tertiary

- **Verified Green:** Accepted evidence and completed remediation only.
- **Caution Amber:** Limitations, metadata-only evaluators, expiring evidence, and conditional decisions.
- **Failure Red:** Failed evaluations, rejected mappings, unresolved blockers, and destructive actions.

### Neutral

- **Assurance Ink:** Text, full borders, hard shadows, and selected navigation.
- **Ledger Paper:** Primary canvas and evidence documents.
- **Quiet Surface:** Secondary toolbars, table headers, and grouped metadata.
- **Muted Ink:** Supporting copy and non-critical metadata. Never use it below accessible contrast.

### Named Rules

**The Two Signal Rule.** Teal means trusted context. Orange means action. Do not use either as decoration.

**The Status Is Text Rule.** Color never carries state alone. Every state includes a plain-language label and, where useful, an icon.

## 3. Typography

**Display Font:** Raleway with a system sans fallback
**Body Font:** Raleway with a system sans fallback
**Label/Mono Font:** The platform monospace stack for hashes, IDs, metrics, thresholds, and timestamps

**Character:** Raleway preserves the existing geometric confidence, while the monospace data voice separates machine evidence from explanatory prose. Extreme weights are reserved for hierarchy, not applied to every line.

### Hierarchy

- **Display** (900, 2.25rem, 1.05): Page titles and decisive empty-state instructions only.
- **Headline** (800, 1.5rem, 1.15): Major workbench regions and review steps.
- **Title** (750, 1rem, 1.3): Evidence names, evaluator names, and table section labels.
- **Body** (500, 0.9375rem, 1.55): Explanations and review notes, capped at 70ch.
- **Label** (800, 0.75rem, 0.08em tracking): Short uppercase metadata labels and navigation groups.
- **Data** (600, 0.8125rem, 1.4): Hashes, versions, thresholds, timestamps, and aligned metrics with tabular numerals.

### Named Rules

**The Evidence Voice Rule.** Human explanation uses the sans voice. Machine identity and measured output use the monospace voice.

## 4. Elevation

Depth is structural, not atmospheric. Surfaces use full borders and hard offset shadows to distinguish interactive work areas from the canvas. Tonal layering handles passive grouping. Blur shadows, glows, translucent glass, and floating decorative surfaces are prohibited.

### Shadow Vocabulary

- **Control lift** (`4px 4px 0 #101614`): Buttons, compact launchers, and selected filters.
- **Workbench lift** (`6px 6px 0 #101614`): Primary working panels and evidence passports.
- **Decision lift** (`10px 10px 0 #101614`): One page-level release or approval gate only.

### Named Rules

**The Earned Shadow Rule.** A shadow means the surface can be acted on or contains a consequential decision. Passive statistics stay flat.

## 5. Components

### Buttons

- **Shape:** Square and decisive with no corner radius.
- **Primary:** Signal Orange, 2px Assurance Ink border, 44px minimum height, and control-lift shadow.
- **Hover / Focus:** Hover translates into the shadow by 2px. Focus uses a visible 2px outer ring. State transitions last 150 to 200ms.
- **Secondary:** Ledger Paper with an Assurance Ink border and the same physical interaction.
- **Destructive:** Failure Red is reserved for irreversible actions and always names the object affected.

### Chips

- **Style:** Square, compact, and fully bordered. Use for capability state, review state, and filters only.
- **State:** Selected chips invert to Assurance Ink. Status chips use both text and a semantic icon.

### Cards / Containers

- **Corner Style:** Square by default. A 2px radius is allowed only for native focus outlines.
- **Background:** Ledger Paper for documents, Quiet Surface for grouped metadata.
- **Shadow Strategy:** Use workbench lift only for active evidence, review, or launch surfaces.
- **Border:** 2px for components, 4px for decision gates and major workbench boundaries.
- **Internal Padding:** 16px compact, 20 to 24px standard, 32px only for empty states.

### Inputs / Fields

- **Style:** Ledger Paper, 2px Assurance Ink border, square corners, 44px minimum height.
- **Focus:** Border remains stable and receives a visible teal outer ring. Do not change layout width on focus.
- **Error / Disabled:** Error includes Failure Red text plus an explicit message. Disabled controls remain legible and explain why they are unavailable.

### Navigation

- Organize around Systems, Test Lab, Evidence and Controls, Assurance, and Organization.
- Active items invert to Assurance Ink with a Signal Orange hard shadow.
- Collapsed navigation retains tooltips and the same task order.
- Mobile navigation uses one standard sheet pattern and preserves the selected system context.

### Evidence Passport

An Evidence Passport is the signature component. It begins with subject, evaluator, result, review state, and freshness. Its next visible layer shows threshold, versions, scope, limitations, and artifact integrity. Framework mappings, remediation, and reruns follow. It never leads with a generic score.

## 6. Do's and Don'ts

### Do:

- **Do** show subject, evaluator version, threshold, result, artifact hash, reviewer, and freshness on every evidence detail surface.
- **Do** label evaluators as validated, metadata-only, external-provider, unavailable, or insufficient-data.
- **Do** use full 2px or 4px borders, hard shadows, strong alignment, and restrained teal/orange signals.
- **Do** keep the selected organization and AI system visible through every test, review, and export workflow.
- **Do** make tables keyboard navigable and preserve labels at 200% zoom.

### Don't:

- **Don't** build generic AI governance suites around inventories, questionnaires, and percentage-readiness dashboards.
- **Don't** use generic AI tool marketing, chat-first copilots, floating sparkle icons, or feature claims without test evidence.
- **Don't** use purple gradients, neon-on-black cyber styling, glassmorphism, soft card clouds, or ornamental animation.
- **Don't** infer compliance certificates or green pass states from missing data, provider availability, or unreviewed mappings.
- **Don't** use isolated test forms that return transient results without subject identity, provenance, artifact hashes, or a review path.
- **Don't** use gradient text, colored side-stripe borders, nested cards, or repeated icon-heading-description card grids.
