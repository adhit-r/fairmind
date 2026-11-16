# fairmind CLI

The release gate and fairness tests from a terminal or a CI job. One dependency, `httpx`.

```bash
pipx install fairmind-cli
# from a checkout of this repository: pipx install ./apps/cli
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...        # minted at POST /api/v1/auth/api-keys, valid 365 days
```

## Commands

```bash
fairmind systems
fairmind gate --system <id>                       # exit 0 go, 2 conditional go, 1 no go
fairmind gate --system <id> --allow-conditional   # exit 0 on conditional go
fairmind gate --system <id> --require-approval    # exit 1 unless the release decision is approved
fairmind test --system <id> --file predictions.csv \
    --outcome repaid --prediction approved --score score --attributes gender,region
fairmind test ... --gate                          # exit by the gate's verdict after the run
```

`test` uploads the CSV, runs disparate impact, demographic parity, equal opportunity, equalized odds and calibration per attribute with bootstrap intervals, and stores the result as measured evidence on the system. `gate` reads the release gate: five checks, each proven, attested or open, a confidence, the verdict from the impact-by-confidence matrix, and the latest release decision (`approvalStatus`: not requested, pending, approved or rejected). A rejected decision makes the verdict no go until a reviewer approves a new request. With `--require-approval` an approval with conditions counts as approved: an approved conditional go exits 0.

Exit code 3 means the command itself failed: no network, no key, wrong system id, a column that is not in the file. Add `--json` to any command for the raw response.

## Models on a private network

Behaviour tests (prompt injection, jailbreak, leakage, over-refusal, output bias) normally have the FairMind server call the model, which needs a public https endpoint. When the model only answers inside your network, run the test from a machine that can reach it:

```bash
export FAIRMIND_API_KEY=...         # a FairMind key of a manager in the organisation
export FAIRMIND_TARGET_AUTH=...     # the model's own key, if it needs one; sent only to the model
fairmind eval run EV-SEC-01 --system <id> --local
```

First set the system's connection, on its page, to "A runner inside your network" with the model's URL as this machine sees it (for example `http://10.0.4.12:8000/v1`), the model name or request template, the system prompt and the intended use. FairMind never calls that URL and never stores the model's key.

The run itself stays on FairMind: it writes the probes, judges the answers with your organisation's AI provider and stores the result as evidence like any behaviour test. The CLI picks up each prompt over https, sends it to the model (four at a time, 60 seconds each) and posts the answer back. Nothing connects in to your network. The stored run records that its answers came through your runner. If the CLI stops, the remaining probes fail within a minute and the run is stored as insufficient.

## Getting a system ready for a framework audit

One command reads where a system stands against a framework and does what can be done from here:

```bash
fairmind audit ISO42001 --system <id>                                  # read only: open clauses and the evaluations that test them
fairmind audit ISO42001 --system <id> --run --inputs plan.json --share # run them, build the pack, mint the auditor link
```

It reads the clause map for that framework, then finds the catalogue evaluations that test each open clause and shows, per evaluation, this system's latest result and what it needs to run (files and params, or nothing for a behaviour test). With `--run` it runs every mapped evaluation that has not passed for this system. An evaluation that needs files or params runs only when `--inputs` supplies them; otherwise it is skipped and the exact `fairmind eval run ...` line is printed. One failure does not stop the rest. `--local` runs behaviour tests through this machine, as in the section above. `--pack` builds the inspection pack after the runs, so it freezes their evidence; `--share` also mints the auditor link. It ends by reading the clause map again and listing each clause still open with the gate check it waits on. Exit 0 when no clause of the framework is open, 1 when any is.

`plan.json` gives each evaluation its files (paths relative to the plan file) and params; `connection: true` reads the organisation's agent platform instead of files. `fairmind eval show <id>` lists what an evaluation takes.

```json
{
  "EV-DAT-04": {"files": {"dataset": "data/train.csv"}, "params": {"rules": {"region": "required"}}},
  "EV-TST-01": {"files": {"predictions": "data/preds.csv"}, "params": {"baseline": 0.81}}
}
```

A clause's state comes from the release gate's five checks (fairness, data governance, human oversight, monitoring, environmental). A passing evaluation is stored and hashed into the pack as evidence, but it does not close its clause on its own: the clause closes when its gate check has evidence. For ISO 42001 every mapped evaluation reads files (datasets, predictions, logs, lineage records), so `--run` does nothing for it without `--inputs`.

## In GitHub Actions

```yaml
- uses: adhit-r/fairmind/.github/actions/fairmind-gate@main   # in this repository: ./.github/actions/fairmind-gate
  with:
    system: ${{ vars.FAIRMIND_SYSTEM_ID }}
    api-url: ${{ vars.FAIRMIND_API_URL }}
    api-key: ${{ secrets.FAIRMIND_API_KEY }}
    predictions: artifacts/predictions.csv       # optional: run the test first
    outcome: repaid
    prediction: approved
    attributes: gender,region
    require-approval: "true"                      # optional: fail unless the release decision is approved
```
