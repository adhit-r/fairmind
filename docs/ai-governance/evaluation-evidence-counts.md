# What a catalogue evaluation run counts for

Status: approved 2026-11-17

An auditor reading a FairMind release gate, a system's Requirements tab, an inspection pack or `fairmind audit` output will ask one question: which measured results moved this status, and why. This page is the answer, and the rule the code follows.

## Where things stood (main after PR #514; PR #521 merged while this was built)

PR #514 already made catalogue evaluation runs count:

| Place | What a run does today |
| --- | --- |
| Release gate (`release_gate`, `gate_check`) | A run counts for the gate check its evaluation's common control maps to. FMC-FAI-01 (fairness testing) feeds "Fairness measured", FMC-DAT-01, FMC-OVS-01, FMC-MON-01 likewise. Passed proves, failed blocks a plain go until that evaluation passes again, insufficient counts for nothing, a material change makes older runs stale. |
| Per-system clause map (`clause_map_service.clause_map`) | Every active clause of a framework is listed (65 for ISO 42001). A run reaches the clauses its common control's crosswalk names. A Satisfies link can prove a clause; any weaker link gives partial at most. |
| Requirements tab, auditor packs, `fairmind audit` status lines | Read the clause map, so they show the above. |

So a passed EV-FAI-05 (LLM output bias, common control FMC-FAI-01) already turns "Fairness measured" green, and moves ISO 42001 A.5.4 and A.7.4 to partial (crosswalk relation: Supports). For the behaviour suite a pilot runs through the private-network runner:

| Evaluation | Common control | ISO 42001 clause it moves today |
| --- | --- | --- |
| EV-FAI-05 LLM output bias | FMC-FAI-01 | A.5.4, A.7.4 (partial) and the fairness gate check |
| EV-SEC-01, EV-SEC-03, EV-SEC-04 | FMC-AGT-02 | A.6.2.4 (partial) |
| EV-OFF-08 Over-refusal | FMC-TST-01 | A.6.2.4 (partial since #521: the crosswalk link is Satisfies, but EV-OFF-08 does not test A.6.2.4) |

## The gap that remains: two maps that disagree

The catalogue links an evaluation to clauses in two ways:

1. **Common control crosswalk** (`evaluation.commonControl` -> `crosswalk`): used by the gate and the clause map.
2. **Direct tests** (`evaluation.tests`, a list of requirement keys): used by journeys (`/packs/journeys/{fw}`: requirement status and the evaluations listed per requirement), by `/packs/evaluations` (`tests`), and by `fairmind audit` to pick which evaluations to suggest and run for an open clause.

They disagree in both directions:

- `fairmind audit --framework iso42001` suggests evaluations by direct tests only. It never lists the behaviour suite above for ISO 42001 (none of them names an ISO clause directly), even though each moves an ISO clause in the clause map. It does list EV-DAT-01 for A.6.2.6, runs it, and A.6.2.6 stays open, because EV-DAT-01's common control does not reach A.6.2.6. The CLI prints an apology line for exactly this case.
- The ISO 42001 journey lists evaluations for 6 clauses; the clause map lets evaluations reach 39.
- A clause can be partial on a system's Requirements tab from an evaluation the journey page does not list under it.

## The rule (one source of truth)

An evaluation **counts toward** a clause through either link:

- its common control's crosswalk link, at that link's relation (Satisfies, Partially satisfies, Supports, Aligns with), capped at Supports when the evaluation does not test that clause itself (the rule PR #521 introduced), and
- a direct test link, at a new relation **Tests**, ranked between Partially satisfies and Supports.

Where both exist, the stronger one wins. So a clause is proven by an evaluation only when the evaluation tests it and its control's crosswalk link satisfies it. One function in `clause_map_service` computes this; the clause map, journeys, `/packs/evaluations` and `fairmind audit` all read it.

How far a run moves a clause is unchanged:

- Only a passed, measured run with confidence at least 0.70 is proven. Catalogue runs are stored measured at 1.0; an insufficient run is stored at 0.0 and counts nowhere.
- A clause is proven only through a Satisfies link, which for an evaluation also means it tests the clause. Partially satisfies, Tests, Supports and Aligns with give partial at most. Reason: a passing test shows the control works for this system; it does not on its own show the management-system clause (scope, roles, records) is met. A reviewer still maps evidence for that.
- A failed run makes every clause it reaches fail until that evaluation passes again.
- A material change to the system makes older runs stale.

**Which evaluations satisfy "Fairness measured"**: every catalogue evaluation whose common control is FMC-FAI-01, decided by the catalogue rather than a hard-coded list. The ones FairMind can run today are EV-FAI-03 (intersectional slices), EV-FAI-04 (counterfactual fairness) and EV-FAI-05 (LLM output bias). EV-FAI-01, -02, -06 and -07 are read from CSV fairness runs.

## Changes

Backend
1. `clause_map_service.evaluation_links(evaluation_id) -> {requirement key: relation}` implements the rule; add "Tests" to `RELATION_RANK`.
2. Clause map: each evaluation run reaches clauses through `evaluation_links`. `release_gate` lists every evaluation's newest passed or failed run (today it lists only runs no gate check counts), so a fairness evaluation's direct test links reach their clauses too. Gate-check entries stay as they are.
3. Pack catalogue: an evaluation's requirement set (`tests`, which drives journey coverage, per-requirement evaluation lists, pack and bundle counts) comes from `evaluation_links`. `/packs/evaluations` and the journey keep the field name `tests` / `evaluations` and add `relation` to each entry.
4. The framework list a clause map can be asked for (`clause_frameworks`) includes every framework an evaluation reaches, not only those the five gate checks reach.
5. CSV path, not weakened: today a passing EV-FAI-05 filed after a failing CSV fairness run hides that failure, because the gate reads only the newest fairness record's result. Make a measured CSV fairness failure stand until a newer CSV fairness run passes, the same rule evaluation runs already follow.

CLI
6. `fairmind audit` picks evaluations from `tests` (PR #521 had it rebuild the crosswalk from `/packs/controls`, a second copy of the rule; that copy goes): any link moves an open clause, only a Satisfies link can take a partial one further. Remove the apology line, and show each suggested evaluation's relation (`proves` for Satisfies, `partial` otherwise) so the user knows whether a pass will close the clause or only move it to partial.

Frontend (labels only; mockup below for sign-off)
7. Journey requirement row: each listed evaluation gets the relation pill workflows already show, strongest relation first. A clause can now list many evaluations (ISO 42001 A.6.2.4: 37), so the row shows those with a result first, then the strongest, five in all, and the rest behind an "N more evaluations" disclosure, the same `<details>` pattern the evaluations list uses.
8. Evaluations list and detail: "Requirements it tests" becomes "Counts toward", each entry with its relation pill, strongest first.

```
Journey, ISO 42001, A.6.2.4 Verification and validation      Status: Tested
  Covered or tested by
    Pre-deployment evaluation              [Satisfies]
    Agent workflow testing                 [Supports]
    ...(workflows as today)
    Over-refusal                           [Supports]   Passed
    Direct prompt injection                [Supports]   Passed
    Task accuracy                          [Satisfies]  Not run
    Agent task success                     [Satisfies]  Not run
    Release regression suite               [Tests]      Not run
    > 32 more evaluations

Evaluations list, EV-SEC-01 Direct prompt injection
  Counts toward  > 91 requirements
    OWASP LLM01  Prompt injection   [Tests]
    AIUC1 A006   ...                [Satisfies]
    EU AI Act Art 15                [Partially satisfies]
    ISO 42001 A.6.2.4               [Supports]
    ...
```

No new tables, no migration, no new endpoint.

## Effect on counts (requirements an evaluation can reach)

| Framework | Active | Direct tests today | New rule |
| --- | --- | --- | --- |
| ISO 42001 | 65 | 6 | 39 |
| NIST AI RMF | 72 | 11 | 58 |
| EU AI Act | 47 | 17 | 34 |
| RBI FREE-AI | 33 | 0 | 15 |

Journey coverage counts rise to match what the clause map already shows per system; most of the new links are Supports (partial at most).

## Tests (pytest, Postgres via `FAIRMIND_TEST_POSTGRES_URL`)

- A passed EV-FAI-05 run stored for a system turns the gate's fairness check proven (measured, 1.0) and moves ISO 42001 A.5.4 and A.7.4 from open to partial, read through the system's gate and clause map endpoints.
- A passed EV-DAT-01 moves A.6.2.6 to partial (direct test link); a passed EV-TST-01 proves A.6.2.4, a passed EV-OFF-08 makes it partial.
- For every evaluation, the clause keys the clause map reaches equal the requirement keys journeys and `/packs/evaluations` list.
- A failing CSV fairness run still blocks a plain go after a later passing EV-FAI-05.
- `fairmind audit` marks each suggestion `proves` or `partial` and takes evaluations from the API's `tests`.

## Not in scope

- Policy rule facts (`governance_evidence_runs`): catalogue runs already write a row there; unchanged.
- New gate checks for security. Security suites move clauses, not gate checks; adding a "Security tested" gate check changes every organisation's verdict and needs its own decision.
- Editing crosswalk relations in `catalogue.json`.
