# FSE 2027 industry paper: data and scripts

Recomputes every number in "When Coding Agents Merge 19 Pull Requests a Day: Which Guardrails Held in a
Nine-Day Release Sprint" (FSE 2027 Industry Track submission) from public sources. All day boundaries are UTC.

```bash
cd research/fse-2027-industry/data
# Commits, AI co-author trailers, merged PRs per day, test runs, releases, Scorecard
python ../analysis/compute_metrics.py --start 2026-11-01 --end 2026-11-09 --tz +00:00
# Root causes of the failed test runs
mkdir -p logs && tail -n +2 failed_runs.csv | cut -d, -f1 | xargs -I{} sh -c 'gh run view {} -R adhit-r/fairmind --log-failed > logs/{}.log'
gh run list -R adhit-r/fairmind --workflow tests.yml --created 2026-10-31..2026-11-11 --limit 2000 \
  --json databaseId,headBranch,createdAt,conclusion > all_runs.json
python ../analysis/classify_ci_failures.py --runs failed_runs.csv --logs logs --all-runs all_runs.json
# Pull requests: size, time to merge, reviews, check state at merge, commits pushed after opening
python ../analysis/pr_analysis.py --ci-failures ci_failures.csv
# Dependabot and code-scanning alerts (needs access to the repository's alerts)
python ../analysis/security_alerts.py > alerts_summary.json
```

Needs `git` with `origin/main` fetched and an authenticated `gh`.

| File in `data/` | What it holds |
|---|---|
| `metrics.json`, `daily.csv` | commit, pull request, test-run, release and Scorecard figures |
| `failed_runs.csv`, `ci_failures.csv`, `ci_failures_summary.json` | the 66 failed test runs and their classified causes |
| `prs.csv`, `pr_summary.json` | one row per merged pull request; the merge-gate and timing figures |
| `commits_after_open_labelled.csv` | the 118 commits pushed after a pull request opened, labelled by what prompted them (from headlines, with AI assistance, one rater) |
| `alerts_summary.json` | Dependabot and code-scanning counts |
| `scorecard_first_run.json` | per-check scores from the first Scorecard run on 5 November 2026 |

GitHub keeps Actions logs for 90 days and the Scorecard artifact for less, so the committed files hold the
results computed on 10 November 2026. The branch ruleset's history (when status checks became required) is
read with `gh api repos/adhit-r/fairmind/rulesets/7609395/history`, which needs admin access.
