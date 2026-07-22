# FairMind Assurance Trailer — Design Specification

## Objective

Create a second, materially stronger FairMind launch film that works simultaneously for three audiences:

- Enterprise AI and GRC leaders deciding whether FairMind belongs in their assurance program.
- Technical evaluation teams deciding whether the product reflects how real testing works.
- Investors and general launch audiences deciding whether the category and product are memorable.

The film must broaden the first video's evidence-passport story into FairMind's full product boundary: evaluating models, generated content, agents, and multimodal systems, then turning those results into governed decisions and reusable evidence.

## Approved Direction

Use a polished assurance-trailer treatment rather than a feature walkthrough or high-energy startup advertisement. The trailer should feel cinematic through pacing, composition, sound, and decisive cuts while remaining grounded in real FairMind product surfaces and carefully bounded claims.

The central promise is:

> Test every layer. Govern the whole system.

The closing category line is:

> FairMind — evidence you can defend.

## Narrative Architecture

The story has three layers that map directly to the intended audiences.

1. **Executive hook:** One AI system can fail across several layers, so a single readiness score is inadequate.
2. **Technical proof:** FairMind coordinates evaluations across model behavior, generated text and code, agent tool use and trajectories, and multimodal inputs.
3. **Governance payoff:** Results retain scope, versions, thresholds, limitations, artifacts, and review status before becoming an accountable deployment decision and reusable Evidence Passport.

The film must not imply that every evaluator is currently validated, that every modality is natively executed by FairMind, or that a technical result proves legal conformity or certification. Capability states and human-review boundaries remain visible.

## Timing and Storyboard

Target duration: 22 seconds. Format: landscape, 1920 × 1080 at 30 fps.

### Scene 1 — One system, many failure surfaces (0.0–2.8s)

Open directly on a governed AI system record, not an abstract logo. Four failure surfaces lock around it: model behavior, generated content, agent actions, and multimodal inputs. The hook lands in two beats:

> One AI system.
> Many ways to fail.

The system remains visually central while the surfaces arrive with distinct motion behaviors. No illegible rapid text or generic technology imagery.

### Scene 2 — Test every layer (2.8–8.0s)

Transition into a real or faithful FairMind evaluation-workbench surface. Show four compact test lanes with concrete examples:

- Model: bias, robustness, red-team behavior.
- Content: text, code, and generated-media checks.
- Agent: permissions, tool actions, and trajectory review.
- Multimodal: image, audio, and cross-modal input boundaries.

Capability truth remains explicit through states such as `validated`, `external_provider`, `metadata_only`, and `unavailable`. The viewer should understand breadth without reading a feature inventory.

### Scene 3 — Preserve the evidence boundary (8.0–13.0s)

Selected evaluator outputs converge into a single Evidence Passport. The artifact visibly binds subject version, evaluator version, threshold, raw artifact digest, limitations, and candidate mapping state. A technical viewer should be able to recognize a real evidence contract within the available hold time.

The governing line is:

> Results are only useful when their boundaries survive.

### Scene 4 — Govern the whole system (13.0–18.3s)

A human review action converts candidate mappings into an accepted evidence state. The system-level decision resolves as `Approved with conditions`, accompanied by visible conditions and a rerun requirement. This demonstrates governance value without promising automatic certification.

The decision should feel consequential, not celebratory. Framework reuse may appear as a secondary handoff after acceptance, but should not dominate the scene.

### Scene 5 — Final promise (18.3–22.0s)

Resolve into a sharp FairMind lockup using the established assurance-ledger system:

> Test every layer.
> Govern the whole system.

Then hold:

> FairMind — evidence you can defend.

The final frame must remain readable as a poster and be baked into frame zero of the delivered MP4.

## Visual Direction

Use the existing FairMind Evidence Workbench design system:

- Ledger Paper `#FBF8F1`
- Assurance Ink `#101614`
- Evidence Teal `#118A72`
- Signal Orange `#FF6B35`
- Square geometry, full borders, hard offset shadows, and monospace evidence data

The visual composition may feel more cinematic than the dashboard, but it must remain recognizably FairMind. Use actual UI crops where available and construct supplementary product views from the same tokens and information hierarchy. Do not use purple gradients, generic AI imagery, glassmorphism, neon cyber styling, soft card clouds, decorative grids, or unreadable microcopy.

Motion should express system relationships: failure surfaces converge into test lanes, test outputs compile into an Evidence Passport, and accepted evidence flows into a governed decision. Each motion must remain deterministic and seek-safe. Reduced-motion support is required in the source composition.

## Audio Direction

Use a restrained cinematic pulse rather than upbeat corporate music. The opening should create tension, the test-lane reveal should add forward motion, the passport assembly should receive the strongest tactile product accent, and the final lockup should resolve with authority.

Sound effects are limited to a few structural events: failure-surface lock-in, evaluator selection, passport compilation, reviewer acceptance, and final resolve. Avoid continuous typing, repeated whooshes, notification sounds, or audio that suggests an automatic compliance pass.

## Composition and Asset Boundaries

Build the second film in a timestamped `brag-output-YYYY-MM-DD-HHmmss/` directory so the first film remains intact. The package will contain:

- `brag-plan.md`
- `composition-brief.md`
- `composition/` source and local assets
- `brag.mp4`
- `brag.jpg`
- `share-copy.txt`

Use the existing product film, the current Evidence Workbench screenshot, and active frontend source only as references or reusable product assets. Do not change application behavior or the marketing website as part of this video task.

## Validation and Acceptance Criteria

The second film is complete when:

- Duration is between 20 and 23 seconds at 1920 × 1080 and 30 fps.
- At least one real FairMind UI surface appears clearly.
- Models, generated content, agents, and multimodal systems are all represented.
- Capability truth, provenance, limitations, human review, and conditional decision status are legible.
- Claims remain bounded: no automatic conformity, certification, or unsupported evaluator maturity claims.
- Hyperframes check passes with zero errors, including runtime, layout, motion, and contrast gates.
- A deliberately selected poster is saved as `brag.jpg` and baked into frame zero.
- The first film and its output directory are preserved unchanged.
- Share copy addresses the category, product mechanism, and governance outcome in no more than three sentences.

## Out of Scope

- Replacing or redesigning the Astro marketing website.
- Changing FairMind product functionality.
- Producing vertical or square social variants.
- Voice-over, testimonials, customer logos, certification marks, or unsupported quantitative claims.
