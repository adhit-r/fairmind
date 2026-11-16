# Private-network runner: behaviour tests on models FairMind cannot reach

Status: approved 2026-11-17

## Problem

Behaviour tests (prompt injection, jailbreak, leakage, over-refusal, output bias and the other
`live="target"` engines) call the AI system under test from the FairMind server. The endpoint must be
public https (`llm._public_https`, checked on save and on every call). SQ1 Security, the first pilot,
runs its models on private addresses, so none of these tests can run, and EV-SEC-01, EV-SEC-03,
EV-SEC-04 and EV-OFF-08 have no file-upload alternative at all.

## Decision

The test still runs on the FairMind server, unchanged. Only the one call to the system under test is
relayed: the CLI, started inside the customer's network, picks up each prompt from FairMind, sends it
to the model, and posts the answer back. All traffic is outbound from the customer to FairMind over
https. Nothing is opened inbound.

- Probe writing, judging, scoring and the stored `evaluation_run` evidence stay server-side and use
  the existing engines as they are (no engine changes). The judge is the organisation's AI provider,
  as today.
- The model's auth value stays on the customer's machine (`FAIRMIND_TARGET_AUTH`). FairMind never
  stores or sees it.
- No new service, queue or table. The relay lives in the server process for the life of the job,
  like the background job itself (the API runs one worker; see the Dockerfile note).

```
FairMind server (job)                    customer network
  engine -> ask(prompt) --pending-->  GET  /evaluation-jobs/{id}/prompts   <- fairmind eval run --local
                                          CLI calls the model at 10.x.x.x
  engine <- answer      <--posted---  POST /evaluation-jobs/{id}/answers
  judge, score, store evidence (target.via = "runner")
```

## Changes

### Connection settings (`system_targets.py`)

- New field `via`: `fairmind` (default, today's behaviour) or `runner`.
- With `via=runner` the URL may be any http(s) address (private is fine); the server never fetches
  it, so the public-https guard does not apply. No auth value is accepted or stored.
- `POST /ai-systems/{id}/target/test` answers 409 for a runner connection, naming the CLI command.
- `ask()` refuses a runner connection, so no code path can make the server call it.

### Runs (`evaluation_runs.py`)

- `POST /evaluations/{id}/runs` with `mode=live` and `runner=1`: for a system whose connection is
  `via=runner`, the job's call to the system under test goes through the relay. Without `runner=1`
  (a run started from the app) it answers 409 with the command to run, rather than a job that waits
  for nobody.
- `GET /evaluation-jobs/{job_id}/prompts`: the job's status and progress, and the prompts waiting
  for an answer (`[{id, prompt}]`).
- `POST /evaluation-jobs/{job_id}/answers`: `{answers: [{id, answer} | {id, error}]}`. Each answer up
  to 1 MB, as for direct calls. Unknown or late ids are ignored.
- Both need a manager of the job's organisation, the same as starting a run.
- If the runner stops polling for 60 seconds, the remaining prompts fail at once as "The runner
  stopped answering" and the run is recorded as insufficient, the same as an unreachable endpoint.
- Evidence records `target: {kind, url, via: "runner"}`, so an auditor can see the answers were
  relayed by the customer's own runner.

### CLI (`apps/cli`)

```
export FAIRMIND_API_KEY=...            # a manager's FairMind key
export FAIRMIND_TARGET_AUTH=...        # the model's key, never sent to FairMind
fairmind eval run EV-SEC-01 --system <id> --live --local
```

`--local` reads the system's saved connection (URL, model or request template, system prompt),
starts the run, answers prompts four at a time (the engines' own concurrency) by calling the model
the same way the server would (OpenAI-compatible or HTTP template, 60 s timeout), and prints the
result as `eval run` does now. Exit codes unchanged.

### App (one panel, mockup attached)

The system page's "Connection for behaviour tests" panel gains a choice of who calls the system. For
"A runner inside your network": the URL help says FairMind never calls it, the auth field is replaced
by a note about `FAIRMIND_TARGET_AUTH`, and the test button is replaced by the command to copy.
Running the test from the app shows the same command (the 409 message).

## Not in this change

- MLflow discovery through the runner (`fairmind runner mlflow`, posting registry pages to the
  connector's upload endpoint). Same pattern; follow-up unless SQ1 needs it for the pilot.
- A long-lived runner daemon that picks up runs started from the app. Add when a customer wants to
  start private runs from the browser.
- SDK support (`run_evaluation(local=True)`).
- Multiple API workers: the relay would move to a table. The Dockerfile already pins one worker.
