# fairmind CLI

The release gate and fairness tests from a terminal or a CI job. One dependency, `httpx`.

```bash
pipx install ./apps/cli            # or: pip install ./apps/cli
export FAIRMIND_API_URL=https://fairmind.example.com
export FAIRMIND_API_KEY=...        # minted at POST /api/v1/auth/api-keys, valid 365 days
```

## Commands

```bash
fairmind systems
fairmind gate --system <id>                       # exit 0 go, 2 conditional go, 1 no go
fairmind gate --system <id> --allow-conditional   # exit 0 on conditional go
fairmind test --system <id> --file predictions.csv \
    --outcome repaid --prediction approved --score score --attributes gender,region
fairmind test ... --gate                          # exit by the gate's verdict after the run
```

`test` uploads the CSV, runs disparate impact, demographic parity, equal opportunity, equalized odds and calibration per attribute with bootstrap intervals, and stores the result as measured evidence on the system. `gate` reads the release gate: five checks, each proven, attested or open, a confidence, and the verdict from the impact-by-confidence matrix.

Exit code 3 means the command itself failed: no network, no key, wrong system id, a column that is not in the file. Add `--json` to any command for the raw response.

## In GitHub Actions

```yaml
- uses: ./.github/actions/fairmind-gate
  with:
    system: ${{ vars.FAIRMIND_SYSTEM_ID }}
    api-url: ${{ vars.FAIRMIND_API_URL }}
    api-key: ${{ secrets.FAIRMIND_API_KEY }}
    predictions: artifacts/predictions.csv       # optional: run the test first
    outcome: repaid
    prediction: approved
    attributes: gender,region
```
