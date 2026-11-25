# Promo plan: FairMind

## What is this app?
An open-source AI assurance workbench for models and agents: it turns governance frameworks into controls, collects evaluation evidence and gates releases, and keeps a system, its tests, evidence and approvals in one reviewable record.

## The angle
**One question, answered with a record.** Every AI release comes down to the question FairMind's docs open with: *may this system ship, and what is the evidence?* The film follows one real system from the public demo, the SST-2 sentiment classifier (`distilbert-base-uncased-finetuned-sst-2-english`), from being found, to being tested, to its evidence, to the release gate, to a person deciding. It ends on the product's one rule: an evaluation result is evidence for a decision, never the decision itself. A person decides.

Every frame of product is the real app, cut from the narrated tour recordings of the live demo. No invented numbers: the only figures on screen are the ones the recordings show (109 evaluations in the catalogue, the 91.1% SST-2 accuracy evidence item, the fairness test on the Equity Evaluation Corpus).

## Hook (0-5s)
Warm grey screen, ink type, set large and quiet:
"May this AI system ship?" ... beat ... "And what is the evidence?"
The second line arrives under the first. No logo yet; the question is the hook.

## Key moments
- Discovery: real Hugging Face models listed as "Found, not registered", with Register it buttons.
- Home board: three systems against every release check; cursor clicks a cell and the drawer opens.
- Evaluations catalogue: 109 evaluations grouped by pillar, panel opens with metric, threshold and results by system.
- Evidence: the sentiment classifier's three items (fairness test, model card, accuracy run) with confidence and source.
- System file: the release gate scoring each check, and "How the verdict was reached".
- Decisions: the pending release request; decided by someone other than the person who asked.

## Outro
"The result is evidence. A person decides." Then the FairMind mark, name, "Open-source AI assurance for models and agents", "Try the live demo: app.fairmind.xyz", "AGPL-3.0, github.com/adhit-r/fairmind".

## User flow worth showing
Find a system -> see it against every release check -> test it -> read its evidence -> gate -> a person decides.

## Tone
- Preset: polished
- Creative direction: a quiet instrument film. Calm, precise, trustworthy, like the app itself.
- Interpretation: long settled holds, soft crossfades and slow push-ins on the recordings; one idea per scene; type does the talking because LinkedIn autoplays muted.

## Format
- Primary: 4:5, 1080x1350 (LinkedIn feed). Headline type in the top third, the recording in a 14px-corner white card with soft shadow below it, slowly pushing in on the part of the screen that matters.
- Secondary: 16:9, 1920x1080 (website, YouTube, LinkedIn page). Same scenes, type left, recording right / full width.
## Duration: about 62s

## Visual identity (from the product)
- Background: #f4f4f2 (`--fm-bg`)
- Text: #15171a ink, #5a5f68 secondary, #9096a0 labels
- Accent: #ff6b35 brand orange, used only for one small mark per scene (an underline, a dot), never a fill
- Status green #1f9d7a (from the logo) for the "go" moment only
- Display and body font: Figtree, semibold headings with tight tracking
- Strongest visual element: the Home board grid of systems against release checks

## Share copy (draft)
See `share-copy.txt`.

## Audio direction
- Role: warm, low bed; restraint over energy
- Music: original bed composed for this video in `music/compose.py` (synthesised, no samples, ~97 BPM, beat grid anchored to the hook and logo)
- Treatment: fade in under the hook, sit low through the product scenes, short swell into the outro, fade out over the logo
- SFX: sparse, soft UI ticks only on the simulated clicks already in the recordings; no whooshes
- Restraint rule: nothing that sounds like a game or an ad jingle

## Storyboard (4:5)

| # | Scene | Time | On screen (type) | Product footage |
|---|---|---|---|---|
| 1 | Question | 0-5s | "May this AI system ship?" then "And what is the evidence?" | none |
| 2 | Answer | 5-9s | FairMind mark. "One reviewable record: the system, its tests, its evidence, its approvals." | none |
| 3 | Find | 9-17s | "Find the AI you have not registered." small: "Discovery reads MLflow, GitHub and Hugging Face." | inventory/discovery: Found, not registered list |
| 4 | See | 17-25s | "Every system, against every release check." small: "Live. Re-read every minute." | home/home: board, cursor clicks a cell, drawer opens |
| 5 | Test | 25-33s | "109 evaluations, grouped by pillar." small: "Metric, threshold and results by system." | testing/evaluations: catalogue, panel opens |
| 6 | Evidence | 33-41s | "Every result becomes evidence." small: "Where it came from, and how much it counts." | records/evidence: sentiment classifier items |
| 7 | Gate | 41-49s | "A release gate reads it check by check." small: "EU AI Act, ISO/IEC 42001, NIST AI RMF, RBI FREE-AI." | inventory/system-file: release gate, verdict |
| 8 | Decide | 49-56s | "The result is evidence. A person decides." small: "Decided by someone other than the person who asked." | release/decisions: pending request opens |
| 9 | Outro | 56-62s | Mark + FairMind. "Open-source AI assurance for models and agents." "Try the live demo: app.fairmind.xyz" "AGPL-3.0" | none |

Transitions: soft 0.6s crossfades; each recording enters at 0.97 scale and settles. Recordings are cut from their middle (not their first seconds) and sped up where the tour lingers, never past 1.5x.

Captions: the on-screen type is the full script, so the video reads with sound off. An `.srt` with the same lines is provided for LinkedIn's caption upload.

## Final copy
The on-screen lines as rendered are in `renders/fairmind-promo.srt` (scene 2 shortened to "Answers it with one reviewable record."; scene 7 says "A release gate scores every check." because the recorded system has no framework confirmed yet).
