# FairMind-E Expert Panel: Instrument and Protocol

Everything needed to run the M6 study: the design, the exact questions, the
consent text, the operator procedure, and the handoff to analysis. Build the
artifacts with `build_instrument.py`; import results with
`import_responses.py`.

## 1. Design

Within-subject, two-arm, counterbalanced.

- 15 raters (R01-R15): 5 GRC, 5 ML engineering, 5 ESG.
- 12 profiles (P01-P12) covering all nine decision-matrix cells, with the
  boundary cells doubled. Every profile is validated against the production
  engine, so its expected labels are the engine's own output, not an author's
  opinion.
- Each rater assesses 8 profiles: 4 under the baseline arm and 4 under the
  module arm, on disjoint profile sets. No rater ever sees the same profile
  twice, so recall cannot contaminate the contrast.
- Each profile receives 10 ratings, balanced exactly 5 baseline and 5 module,
  with at least 3 raters from each role.

**Baseline arm.** The rater sees the system description, the declared
boundary, the raw measurement table, the stated measurement source, and any
proposed mitigation or requested exception. No confidence score, no provenance
class, no impact tier, no decision-matrix position, no recommendation, no
control-coverage table.

**Module arm.** Everything in the baseline arm plus the full FairMind-E
output: provenance class, evidence confidence and band, impact tier, matrix
position, recommendation, approval-blocking status, and the ENV-1..ENV-6
coverage table.

The arm contrast is the whole study. A single-condition instrument yields zero
baseline observations and H2 becomes uncomputable after the fact; see
`analysis/DESIGN_NOTES.md`.

## 2. Questions

Asked identically for every item, in this order. Question 4 appears on
module-arm items only.

1. **Release recommendation.** Single choice, required, no free text:
   `go`, `conditional_go`, `no_go`.
   Rubric shown to the rater: go means release with no environmental
   condition; conditional_go means release only with a documented condition
   attached; no_go means do not release on the environmental evidence as filed.

2. **Required evidence.** Multi-select, may be empty:
   which of the following would you require as evidence before release?
   - ENV-1 Assessment boundary declared (system, lifecycle phase, functional unit)
   - ENV-2 Energy accounting (total kWh for the declared boundary)
   - ENV-3 Dual carbon accounting (location-based and market-based kgCO2e)
   - ENV-4 Per-functional-unit efficiency metric
   - ENV-5 Evidence confidence (provenance class and disclosed uncertainty)
   - ENV-6 Mitigation or owned exception for a conditional release

   This drives H2. Present the six options in the same fixed order in both
   arms; do not group, star, or pre-tick any of them.

3. **Decision confidence.** Single choice 1-5, required, where 1 is not at all
   confident and 5 is very confident. This is the rater's certainty about
   their own decision, not the system's evidence confidence. Label it that way
   on the form to prevent conflation.

4. **Manipulation check (module arm only).** Did this item display an evidence
   confidence score? `yes` / `no`. Responses answering `no` are excluded from
   H1 rather than diluting the correlation.

**Timing.** Capture time on item as `time_to_decision_s`, automatically. Do
not ask the rater to self-report it.

## 3. Export contract

One row per rater-item, with these column names exactly:

    rater_id, profile_id, recommendation, controls_required,
    decision_confidence_1_5, time_to_decision_s, confidence_shown

`controls_required` is semicolon-joined (for example `ENV-1;ENV-3;ENV-5`) and
may be empty. `confidence_shown` is required on module-arm rows only. Extra
columns are ignored by the importer. Any survey tool that can export this
shape works; the study does not depend on a particular platform.

## 4. Consent and participant information

Present before the first item; collect an explicit affirmative.

> **What this study is.** You are being asked to review environmental
> evidence submissions for AI systems and decide, for each one, whether the
> system should be released. The study evaluates a governance mechanism, not
> you. There are no right answers that reflect on your competence, and no
> individual results will be reported or shared with your employer.
>
> **What you will do.** You will work through 8 short system profiles and
> answer 3 or 4 questions about each. Expect 45 to 60 minutes in total. You
> may stop at any point without giving a reason.
>
> **What we record.** Your responses, the time spent on each item, and your
> professional role group (governance/risk/compliance, ML engineering, or
> environmental/sustainability). We do not record your name, employer, or
> contact details alongside your responses; your rater identifier is assigned
> by the study team and the linking list is held separately and destroyed
> after data collection closes.
>
> **The profiles are fictional.** Every system, organisation, and measurement
> in this study is synthetic. Nothing you see is a real company's data, and
> your assessments have no consequence for any real deployment.
>
> **How results are used.** Aggregated, anonymised results will appear in an
> academic publication and the underlying anonymised response data may be
> published alongside it for replication.
>
> **Questions or withdrawal.** Contact the study team at the address on this
> page. You may request removal of your responses until the analysis is
> published.
>
> Do you consent to take part on these terms? (yes / no)

Institutional review: confirm whether your institution requires ethics
approval for this study before recruiting. A low-risk professional-judgment
study with no personal data often qualifies for exemption or expedited
review, but that determination belongs to the review body, not the study
team. Record the outcome here before data collection begins.

## 5. Operator procedure

1. Build the artifacts:

   ```bash
   python3 research/fairmind-e/panel/build_instrument.py
   ```

   This writes `packets/R01.md` through `packets/R15.md`, the arm-annotated
   `assignment_plan_arms.csv`, and `gold_checklists.csv`. `--check` validates
   the design without writing.

2. Recruit 15 raters into the three role groups. Avoid drawing all raters from
   one organisation or from the authors' immediate colleagues; a reviewer will
   read a convenience sample as a limitation, and it is one.

3. Assign each rater a stable identifier and send only their own packet. The
   packet order is the presentation order; ask raters not to skip ahead or
   revisit earlier items.

4. Build the survey to the question spec in Section 2 and the export contract
   in Section 3. The packet is the stimulus; the form collects the answers.

5. Raters must work independently. Do not show one rater another's answers,
   and ask them not to discuss the items until the study closes. H3 is an
   agreement statistic and correlated raters invalidate it.

6. Close collection, export the raw responses, and import them:

   ```bash
   python3 research/fairmind-e/panel/import_responses.py --responses raw_export.csv
   ```

   This writes `responses/panel_responses.csv` and
   `responses/coverage_pre_post.csv`, reporting any manipulation-check
   failures, unpaired profiles, and malformed rows rather than repairing them.

7. Run the analysis:

   ```bash
   cd apps/backend
   uv run python ../../research/fairmind-e/analysis/hypotheses.py \
       --panel ../../research/fairmind-e/panel/responses/panel_responses.csv \
       --coverage ../../research/fairmind-e/panel/responses/coverage_pre_post.csv
   ```

## 6. What each hypothesis draws on

| Hypothesis | Source | Requirement this instrument satisfies |
| --- | --- | --- |
| H1 confidence to conservatism | module-arm responses joined to shown confidence | displayed confidence per item, plus the manipulation check that filters items where it was not seen |
| H2 control coverage | both arms, paired per profile | the baseline arm; every profile carries 5 ratings per arm |
| H3 inter-rater agreement | responses, by arm | 10 ratings per profile, at least 3 per role, stable rater ids, closed label set, independent rating |
| H4 mitigation effect | measurement study only | not collected here; do not add H4 items to this survey |

## 7. Claim boundaries

The profiles are synthetic instruments, not measurements of real systems. The
panel measures reviewer behaviour under a controlled contrast; it does not
establish that the mechanism improves real-world release outcomes, and the
paper must not claim that it does. Fifteen raters is sized for feasibility,
not for power against small effects; report the achieved confidence intervals
rather than only the point estimates.
