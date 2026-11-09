# Evaluation engines: real status and build plan

Date: 2026-11-09. Scope: the 109 evaluations in `apps/backend/src/api/routers/pack_catalogue_data/catalogue.json`.

## 1. The website numbers are stale

The homepage table (`apps/website/src/components/home/EvalTable.astro`) shows 10 built, 24 partial, 75 not built.
Those come from the hand-written `engine` field in `catalogue.json`, written before the engine package existed.
The code says otherwise:

| Source of a result | Count | Where |
|---|---|---|
| Engine in the registry, file upload | 28 | `src/application/services/eval_engines/{data,model,ops}.py` |
| Engine in the registry, live probe of the AI system with a judge | 18 | `eval_engines/behaviour.py` |
| Engine in the registry, agent platform configuration audit | 10 | `eval_engines/platform.py` |
| Result rule over an older flow (fairness run, monitoring run, environmental assessment) | 5 | `src/api/routers/evaluation_results.py` `RULES`: FAI-01, FAI-02, FAI-06, FAI-07, ENV-01 |
| **Runnable today** | **61** | |
| Not built | 48 | listed in section 4 |

So 40 evaluations marked "Not found" and 11 marked "Partial" already have engines, while several marked "Engine exists"
(OVS-04 Explanation quality) have service code that no evaluation run calls.

## 2. How far it works (verified 2026-11-09)

| Check | Result |
|---|---|
| Engine, run API, behaviour, sandbox launcher packs and fairness-run tests on a disposable PostgreSQL 18 | 319 passed, including one API run per engine kind (file, live, platform) stored as evidence |
| Known-answer tests (hand-calculated values) | FAI-01, FAI-02 (impact ratio, equal opportunity, equalized odds), DAT-01 (PSI), FAI-05 (WEAT effect size and exact p), SEC-01 (attack success rate) |
| Run API | `POST /evaluations/{id}/runs`, `GET /evaluations/{id}/engine`, `GET /evaluation-jobs/{job_id}`, `GET /evaluation-runs/{evidence_id}` |
| UI | `/compliance/evaluations/[evaluationId]` calls the run API |
| Worker and sandbox (P1) | Not on main. S1 worker API is WIP (`task/p1-s1-worker-api`), S2, S4 and job lifecycle are unmerged branches; S3 input broker and S5 supervisor/signer not started |

Each engine is therefore at most "runs in the API process from an upload or a live probe". None runs unattended in an
isolated worker, and none has been checked against a known-answer dataset.

### Maturity ladder used below

- **L0** specified in the catalogue only
- **L1** engine code with unit tests
- **L2** run through the API and stored as evidence on an AI system (DB tests green)
- **L3** reachable and readable in the UI
- **L4** validated: known-answer fixture or public benchmark reproduces the expected verdict
- **L5** runs in the P1 worker sandbox, signed result

Today: 61 at L1, assumed L2/L3 but unverified in this session; 0 at L4 or L5.

## 3. Plan

### Phase 0: one source of truth and a real verification pass (done 2026-11-09, except UI runs and public benchmarks)

Status: `scripts/export_pack_catalogue.py` now writes `engine` and `codeLocation` from the code, and
`test_catalogue_engine_status_matches_the_code` fails when they drift. "Partial" now means related code with no runnable
engine (13); the website reads 61 / 13 / 35. Still open: a UI run on a non-production stack (L3) and reproducing a
published benchmark result (L4 beyond hand calculations).

1. Stop hand-maintaining `engine` in `catalogue.json`. Add a small script (or a step in the existing catalogue build)
   that writes `engine` from `REGISTRY` plus `evaluation_results.RULES`, and a test that fails when they disagree.
   The website then shows 61 / 48 automatically.
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

### Phase 3: needs the P1 worker and sandbox (18, high effort, after S1/S3/S5 merge)

These run attacks or agent scenarios that must not run in the API process.

- Model-access attacks: SEC-11 extraction, SEC-12 inversion, SEC-13 adversarial evasion, SEC-15 backdoor.
- Agent scenario harness (one harness, many evaluations): TST-05 task success, TST-06 tool-call correctness,
  AGT-02 out-of-scope actions blocked, OVS-01 kill switch, OVS-02 override honoured, OVS-03 escalation triggers,
  SEC-10 unbounded consumption, SLF-02 FairMind agent unauthorised actions, OVS-06 decision-card accuracy, SEC-25 trust exploitation.
- Multi-agent harness: SEC-22 message integrity, SEC-23 cascading failure, SEC-24 rogue agent detection.
- USE-06 coding-agent suite once DEV-03 and the sandbox exist.

### Phase 4: integrate or partner, do not build (6)

Detectors, simulation platforms or restricted probe sets FairMind should not host itself; record their results as evidence.

- OFF-01 deepfake detection, OFF-02 voice-clone resistance, OFF-03 phishing simulation, TRN-02 provenance and watermark detection:
  import results from a detector or simulation vendor.
- OFF-04 sexual abuse material refusal, OFF-05 CBRN uplift refusal: only with a licensed, legally handled probe set from a partner.

## 4. Not built, by phase

| Phase | Evaluations |
|---|---|
| 1 | USE-01, USE-02, USE-05, USE-07, USE-08, USE-09, REL-01, TST-09, INC-01, SLF-03, DAT-09, OVS-04, OVS-05 |
| 2 | DEV-03, MON-02, TRN-01, DAT-10, PRV-05, FAI-08, SEC-09, RSK-02, SEC-08, OFF-07, SEC-26 |
| 3 | SEC-11, SEC-12, SEC-13, SEC-15, TST-05, TST-06, AGT-02, OVS-01, OVS-02, OVS-03, SEC-10, SLF-02, OVS-06, SEC-25, SEC-22, SEC-23, SEC-24, USE-06 |
| 4 | OFF-01, OFF-02, OFF-03, TRN-02, OFF-04, OFF-05 |

Total 48. After phases 1 and 2 the catalogue reaches 85 of 109 runnable without the worker.
