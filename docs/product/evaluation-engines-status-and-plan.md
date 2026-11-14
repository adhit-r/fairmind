# Evaluation engines: real status and build plan

Date: 2026-11-09, updated 2026-11-13 (all 109 runnable). Scope: the 109 evaluations in `apps/backend/src/api/routers/pack_catalogue_data/catalogue.json`.

## 1. Where the numbers come from

The homepage table (`apps/website/src/components/home/EvalTable.astro`) reads the `engine` field in `catalogue.json`, which
`scripts/export_pack_catalogue.py` writes from the code. It read 10 / 24 / 75 when the field was hand-written, and reads
109 / 0 / 0 since 2026-11-13:

| Source of a result | Count | Where |
|---|---|---|
| Engine in the registry, file upload (including sector suites and results read from stored runs) | 49 | `src/application/services/eval_engines/{data,model,ops,suites,assess}.py` |
| Engine in the registry, live probe of the AI system with a judge (OFF-04 and OFF-05 on an uploaded restricted probe set only) | 24 | `eval_engines/behaviour.py` |
| Engine in the registry, agent platform configuration audit | 10 |
| Engine in the registry, results file from the organisation's own sandbox, drill, attack or detector run | 21 | `eval_engines/agentic.py` | `eval_engines/platform.py` |
| Result rule over an older flow (fairness run, monitoring run, environmental assessment) | 5 | `src/application/services/evaluation_results.py` `RULES`: FAI-01, FAI-02, FAI-06, FAI-07, ENV-01 |
| **Runnable today** | **109** | |
| Not built | 0 | section 4 |


## 2. How far it works (verified 2026-11-09)

| Check | Result |
|---|---|
| Engine, run API, behaviour, sandbox launcher packs and fairness-run tests on a disposable PostgreSQL 18 | 319 passed, including one API run per engine kind (file, live, platform) stored as evidence |
| Known-answer tests (hand-derived values, a threshold boundary case and a failing case each) | All 109 runnable evaluations: 104 engines (56 earlier ones, the 23 of phases 1 and 2 and the 25 of phases 3 and 4; file, live and platform forms; `tests/test_known_answer_{data,model,ops,platform,behaviour,phase1,phase2,agentic}.py`) and the 5 older-flow rules (`tests/test_known_answer_rules.py`). Recorded as `maturity: "L4"` in the catalogue from `eval_engines.VALIDATED`, which a test keeps equal to the tests' coverage |
| Run API | `POST /evaluations/{id}/runs`, `GET /evaluations/{id}/engine`, `GET /evaluation-jobs/{job_id}`, `GET /evaluation-runs/{evidence_id}` |
| UI | `/compliance/evaluations/[evaluationId]` calls the run API |
| Worker and sandbox (P1) | Not on main. S1 worker API is WIP (`task/p1-s1-worker-api`), S2, S4 and job lifecycle are unmerged branches; S3 input broker and S5 supervisor/signer not started |

Each engine is therefore at most "runs in the API process from an upload or a live probe". None runs unattended in an
isolated worker, and each is validated against a hand-derived known-answer fixture (L4). Public benchmarks are still open.

### Maturity ladder used below

- **L0** specified in the catalogue only
- **L1** engine code with unit tests
- **L2** run through the API and stored as evidence on an AI system (DB tests green)
- **L3** reachable and readable in the UI
- **L4** validated: known-answer fixture or public benchmark reproduces the expected verdict
- **L5** runs in the P1 worker sandbox, signed result

Today: 109 runnable, all 109 at L4 (the 56 original registry engines, the 5 rules, the 23 Phase 1 and 2 engines and the 25 Phase 3 and 4 engines, each with known-answer, exact-threshold and failing cases; L2/L3 unverified in this session); 0 at L5.

## 3. Plan

### Phase 0: one source of truth and a real verification pass (done 2026-11-09, except UI runs and public benchmarks)

Status: `scripts/export_pack_catalogue.py` now writes `engine` and `codeLocation` from the code, and
`test_catalogue_engine_status_matches_the_code` fails when they drift. "Partial" means related code with no runnable
engine (none left); the website read 61 / 13 / 35 before phases 1 and 2, 84 / 2 / 23 after them, and 109 / 0 / 0 since phases 3 and 4 (2026-11-13). Still open: a UI run on a non-production stack (L3) and reproducing a
published benchmark result (L4 beyond hand calculations).

1. Stop hand-maintaining `engine` in `catalogue.json`. Add a small script (or a step in the existing catalogue build)
   that writes `engine` from `REGISTRY` plus `evaluation_results.RULES`, and a test that fails when they disagree.
   The website then shows the runnable count automatically.
2. Run the 24 DB-backed tests against a disposable local Postgres (never the Neon URL in `.env`).
3. Per engine kind, one end-to-end run on the dev stack: upload or probe, evidence stored, verdict shown in the UI.
   Record the level per evaluation (L1 to L3) in the same generated field, so "partial" means something checkable.
4. Add a known-answer fixture per engine family (fairness, drift, data quality, behaviour judge, platform audit) to reach L4
   for the families the paper and the sales demo rely on first: FAI-01..05, DAT-01, TST-01, SEC-01..04.

### Phase 1: compositions and wiring of code that already exists (13, low effort)

No new measurement, only running existing engines together or wiring existing services.

- Sector suites made of existing engines: USE-01 hiring, USE-02 credit, USE-05 customer service, USE-07 public benefits,
  USE-08 education, USE-09 insurance. Missing parts: USE-02 needs OVS-04, USE-05 needs OVS-03.
- Meta over stored runs: REL-01 release regression (latest result of each required evaluation), TST-09 reproducibility
  (rerun with pinned config, compare), INC-01 incident regression (incidents with a linked run), SLF-03 evidence trace
  completeness (`evidence_authenticity_service.py`), DAT-09 lineage completeness (`model_provenance_service.py`).
- Wire existing services as engines: OVS-04 explanation quality and OVS-05 explanation stability
  (`generative_ai_explainability.py`).

### Phase 2: new engines on the existing file and live frameworks (11, medium effort)

- File engines: DEV-03 security scan of AI-generated code (wrap an installed scanner), MON-02 tool-call anomalies,
  TRN-01 AI disclosure inventory, DAT-10 training data licence, PRV-05 erasure propagation (scan report form),
  FAI-08 accessibility (checklist or axe report upload), SEC-09 vector and embedding weaknesses (probe results upload).
- Live probes with a judge (same pattern as `behaviour.py`): RSK-02 manipulative design, SEC-08 improper output handling,
  OFF-07 information integrity, SEC-26 reconnaissance exposure.

### Phase 3: agent scenarios, multi-agent faults and attacks on models (18, built 2026-11-13 as results engines)

Built in `eval_engines/agentic.py` (USE-06 in `suites.py`) as file engines that compute each metric from the raw results of a run the
organisation does in its own sandbox. Running the attacks and scenarios inside FairMind still needs the P1 worker and sandbox
(S1/S3/S5), since they must not run in the API process.

- Model-access attacks: SEC-11 extraction, SEC-12 inversion, SEC-13 adversarial evasion, SEC-15 backdoor.
- Agent scenario harness (one harness, many evaluations): TST-05 task success, TST-06 tool-call correctness,
  AGT-02 out-of-scope actions blocked, OVS-01 kill switch, OVS-02 override honoured, OVS-03 escalation triggers,
  SEC-10 unbounded consumption, SLF-02 FairMind agent unauthorised actions, OVS-06 decision-card accuracy, SEC-25 trust exploitation.
- Multi-agent harness: SEC-22 message integrity, SEC-23 cascading failure, SEC-24 rogue agent detection.
- USE-06 coding-agent suite once DEV-03 and the sandbox exist.

### Phase 4: integrate or partner, do not build (6, built 2026-11-13 as result imports)

Detectors, simulation platforms or restricted probe sets FairMind should not host itself; their results are recorded as evidence.
OFF-04 and OFF-05 run only on an uploaded restricted probe set, never written by the judge model, and withhold probe and answer text from evidence.

- OFF-01 deepfake detection, OFF-02 voice-clone resistance, OFF-03 phishing simulation, TRN-02 provenance and watermark detection:
  import results from a detector or simulation vendor.
- OFF-04 sexual abuse material refusal, OFF-05 CBRN uplift refusal: only with a licensed, legally handled probe set from a partner.

## 4. Not built

None. Phases 1 and 2 (23 evaluations) and phases 3 and 4 (25, including USE-05 once OVS-03 existed) are built: all 109 are
runnable without the worker. What remains is L5: running phase 3 attacks and scenarios in the P1 worker sandbox with a signed result.

Phase 1 and 2 notes: EV-OVS-04 and EV-OVS-05 read per-case measurements from the model (outputs with the top and bottom-ranked features removed; attributions of paired inputs) instead of calling `generative_ai_explainability.py`, which holds no data to score. The sector suites run their file-based components; behaviour tests that call the system (EV-TST-04, EV-RSK-01, EV-PRV-04) run on their own. EV-REL-01 is the one engine that reads FairMind's stored results (`Engine.collect`).
