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
