# fairmind (Python SDK)

A small typed client for the FairMind API: read the release gate, run fairness tests, record monitoring snapshots and attestations. One dependency, `httpx`.

```bash
pip install fairmind          # or: uv add fairmind; from a checkout: pip install ./apps/sdk
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...   # minted at POST /api/v1/auth/api-keys
```

```python
from fairmind import FairMind, FairMindError

fm = FairMind()  # reads FAIRMIND_API_URL and FAIRMIND_API_KEY

system = fm.systems()[0]["id"]
run = fm.run_fairness(system, "predictions.csv", outcome="repaid", prediction="approved", attributes=["gender", "region"])
gate = run["gate"]
print(gate["verdict"], gate["confidence"])
for check in gate["checks"]:
    print(check["label"], check["state"])
```

## Methods

| Method | Endpoint |
| --- | --- |
| `systems()` | `GET /systems` |
| `gate(system_id)` | `GET /systems/{id}/gate` |
| `clause_map(system_id, frameworks=None)` | `GET /systems/{id}/clause-map`; `frameworks` (for example `["EUAIA", "ISO42001"]`) filters the result |
| `seals(system_id)` | `GET /systems/{id}/seals` |
| `inspect_csv(system_id, path)` | `POST /systems/{id}/fairness-runs/inspect` |
| `run_fairness(system_id, path, *, outcome, attributes, prediction=None, score=None, favorable_label=None)` | `POST /systems/{id}/fairness-runs` |
| `fairness_runs(system_id)` | `GET /systems/{id}/fairness-runs` |
| `run_monitoring(system_id, path, *, attributes, prediction=None, score=None, favorable_label=None)` | `POST /systems/{id}/monitoring-runs` |
| `monitoring_runs(system_id)` | `GET /systems/{id}/monitoring-runs` |
| `attest(system_id, check, statement, reference=None)` | `POST /systems/{id}/attestations` |
| `evaluations(query=None, pillar=None)` | `GET /api/v1/packs/evaluations` |
| `evaluation_engine(evaluation_id)` | `GET /api/v1/packs/evaluations/{id}/engine`: the files and params it takes |
| `run_evaluation(system_id, evaluation_id, files=None, params=None, live=False, source="upload")` | `POST /api/v1/packs/evaluations/{id}/runs`; waits for behaviour-test jobs and returns the stored run |
| `evaluation_runs(evaluation_id, system_id=None)` | `GET /api/v1/packs/evaluations/{id}/runs` |

The evaluation methods act in the organisation from `FAIRMIND_ORG_ID`, or the key's first organisation when it is unset.

`attributes` is a list or a comma-separated string. `run_fairness` and `run_monitoring` need `prediction` (a 0/1 column) or `score` (a 0 to 1 column). Responses are plain dicts typed with `TypedDict`s (`Gate`, `GateCheck`, `ClauseMap`, `FairnessRun`, `MonitoringRun`, ...).

Every failure raises `FairMindError` with `status_code` (`None` when the server could not be reached) and `message` (the server's `detail` when it sent one).

## Tests

```bash
cd apps/sdk && uv run --with pytest pytest -q -p no:cacheprovider tests
```
