# FairMind Evidence Workbench: Marketing Launch Kit

Date: 2026-07-18

## Category

AI assurance evidence workbench

FairMind is not positioned as a certification authority, legal-compliance engine, or proprietary replacement for every evaluator. It is the vendor-neutral evidence layer between real technical tests and accountable governance decisions.

## Positioning

### Primary line

Bring your tests. Produce evidence you can defend.

### Product description

FairMind converts outputs from model, data, LLM, agent, security, provenance, and environmental evaluators into portable Evidence Passports. Each passport preserves the tested subject, tool and metric versions, threshold, artifacts, integrity hashes, result, limitations, reviewer decision, remediation, and superseding rerun.

### Differentiation

Most governance platforms lead with inventories, questionnaires, or readiness scores. FairMind leads with the test result and its chain of custody. It lets teams reuse accepted evidence across versioned framework mappings without turning a technical result into an automatic compliance claim.

## Homepage Copy

### Hero

**Eyebrow:** AI assurance evidence workbench

**Headline:** Bring your tests. Produce evidence you can defend.

**Body:** Convert real evaluation outputs into reviewable Evidence Passports. Preserve provenance, thresholds, artifacts, limitations, human decisions, remediation, and reruns in one system-scoped assurance record.

**Primary action:** Review the evidence workflow

**Secondary action:** Inspect an Evidence Passport

### Proof strip

- Vendor-neutral evaluator adapters
- Immutable run and artifact identity
- Human-reviewed control mappings
- Findings, remediation, and retest history
- Versioned framework reuse
- Reproducible JSON and document packages

### Boundary statement

FairMind prepares and organizes assurance evidence. It does not certify systems, provide legal advice, or infer conformity from an unreviewed technical test.

## Product Story

### 1. Start with a registered AI system

Keep the organization, workspace, intended use, owner, lifecycle stage, model or agent version, and framework assignments visible through every workflow.

### 2. Bring a real evaluation result

Run a supported FairMind evaluator or ingest a result from an external tool. Every adapter declares whether it is validated, metadata-only, external-provider, unavailable, or operating with insufficient data.

### 3. Compile an Evidence Passport

Bind the run identity, evaluator and metric versions, threshold, subject and dataset fingerprint, runtime environment, raw artifact location, digest, result, uncertainty, and limitations.

### 4. Review the candidate mappings

FairMind may propose control mappings. An accountable reviewer accepts or rejects them and records the decision. No evaluator directly changes compliance or approval state.

### 5. Close the assurance loop

Turn failed or limited runs into findings. Link remediation, retest, approvals, and superseding evidence. Export an assurance manifest pinned to the organization, system, framework version, and evidence cutoff.

## Capability Language

Use only these product states:

- `validated`: bounded end-to-end behavior is implemented and test-backed.
- `metadata_only`: the evaluator operates on supplied metadata and does not inspect the underlying media or model behavior.
- `external_provider`: execution and quality depend on a named provider that may be unavailable.
- `unavailable`: the workflow must not be launched until its contract is implemented and verified.
- `insufficient_data`: the evaluator cannot produce a supported result from the supplied evidence.

Never translate provider failure, missing data, empty findings, initialization success, or a mock response into “healthy,” “compliant,” “passed,” or “not biased.”

## Launch Post: Product Thesis

FairMind started as a broad AI-governance dashboard. The market changed, and so did the codebase.

The recovery direction is more specific:

**Bring your tests. Produce evidence you can defend.**

FairMind is becoming a vendor-neutral assurance evidence workbench. It converts real outputs from model, data, LLM, agent, security, provenance, and environmental evaluators into portable Evidence Passports.

Every passport preserves subject identity, versions, thresholds, artifacts, integrity hashes, limitations, reviewer decisions, remediation, and reruns. One accepted passport can support several versioned framework mappings, but a test never auto-declares compliance.

The product is the chain of custody between a real evaluation and an accountable governance decision.

## Launch Post: Product Honesty

An AI-governance tool should never turn missing evidence into a reassuring state.

FairMind now uses an explicit capability vocabulary:

- validated
- metadata-only
- external-provider
- unavailable
- insufficient-data

That distinction matters. A metadata analysis is not image analysis. A provider error is not a pass. A mock result is not evidence. A technical test is not a certificate.

Trust starts when the interface says exactly what the underlying system can prove.

## Launch Post: Evidence Passport

A readiness score cannot tell an auditor what changed.

An Evidence Passport can.

It binds the tested subject, evaluator version, metric, pre-defined threshold, dataset or prompt scope, runtime environment, raw artifact, integrity digest, result, uncertainty, limitations, reviewer decision, remediation, and superseding rerun.

Change the model, data, prompt, threshold, or scope, and FairMind stales only the affected evidence.

Reuse evidence across AIUC-1, EU AI Act, ISO, and NIST mappings. Never reuse an unreviewed claim.

## Announcement Email

**Subject:** FairMind is becoming an AI assurance evidence workbench

FairMind is moving from a broad governance dashboard to a more defensible product: a vendor-neutral workbench for compiling real evaluation outputs into reviewable assurance evidence.

The new product unit is the Evidence Passport. It preserves the complete chain from tested subject and threshold through raw artifacts, limitations, reviewer decisions, remediation, and reruns. Accepted passports can support several versioned framework mappings without converting technical results into automatic compliance claims.

The first recovery sprint focuses on the trustworthy assurance spine and truthful capability states. The second adds evaluator adapters, findings and retest workflows, and reproducible assurance packages.

The principle is simple: bring your tests and produce evidence you can defend.

## Video Copy

### Remotion landscape film

**Title:** FairMind Evidence Workbench: Bring Your Tests

**Description:** A 31-second product film introducing truthful capability states, the Evidence Passport, human-reviewed framework reuse, and the FairMind assurance evidence workbench.

### HyperFrames vertical explainer

**Title:** A Readiness Score Is Not Evidence

**Description:** A narrated 36-second vertical explainer showing why FairMind starts with real tests, preserves the evidence chain, and keeps compliance decisions human-reviewed.

## Podcast Show Notes

**Title:** FairMind Recovery Briefing: From Governance Dashboard to Evidence Workbench

**Summary:** Two synthetic hosts examine the live FairMind capability gaps, the current AI-governance market, the Evidence Passport wedge, framework reuse boundaries, the assurance architecture, the Ponytail code-quality audit, and the two-sprint recovery plan.

**Topics:**

- Why broad feature surface is not the same as evidence-grade capability
- The validated environmental-governance slice
- Broken, mocked, metadata-only, and provider-dependent paths
- Competitor and open-source evaluator landscape
- Evidence Passport identity and integrity model
- AIUC-1, EU AI Act, ISO, and NIST evidence reuse
- Safe integration of the assurance and FairMind-E branches
- Conservative code-deletion sequence
- Sprint acceptance evidence

## Asset Inventory

- `outputs/fairmind-evidence-workbench/assets/fairmind-assurance-ledger-hero.png`: landscape campaign key art.
- `outputs/fairmind-evidence-workbench/assets/fairmind-evidence-passport-social-square.png`: square social key art.
- `outputs/fairmind-evidence-workbench/FairMind_Evidence_Workbench_Strategy.pptx`: editable ten-slide strategy deck.
- `outputs/fairmind-evidence-workbench/FairMind_Evidence_Workbench_Remotion.mp4`: 16:9 motion-graphics film.
- `outputs/fairmind-evidence-workbench/FairMind_Evidence_Workbench_HyperFrames.mp4`: narrated 9:16 explainer.
- `outputs/fairmind-evidence-workbench/FairMind_Evidence_Workbench_AI_Podcast.mp3`: two-host recovery briefing.
- `outputs/fairmind-evidence-workbench/FairMind_Evidence_Workbench_Podcast_Transcript.md`: accessible podcast transcript.

## Visual Guardrails

- Use the warm paper, assurance ink, evidence teal, and signal orange system defined in `DESIGN.md`.
- Use strong full borders, hard offset shadows, and sharp geometry.
- Use teal for trusted context and orange for consequential action.
- Keep product screens task-focused and evidence-dense.
- Do not use purple gradients, neon cyber styling, glassmorphism, soft card clouds, sparkles, robots, brains, or generic AI imagery.
