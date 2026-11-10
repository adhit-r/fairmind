# FSE 2027 industry paper: data and scripts

Recomputes every number in "Hardening and Shipping an Open-Source AI Governance Platform in Nine Days with
Coding Agents: An Experience Report" (FSE 2027 Industry Track submission) from public sources.

```bash
cd research/fse-2027-industry/data
python ../analysis/compute_metrics.py --start 2026-11-01 --end 2026-11-09 --tz +00:00
mkdir -p logs && tail -n +2 failed_runs.csv | cut -d, -f1 | xargs -I{} sh -c 'gh run view {} -R adhit-r/fairmind --log-failed > logs/{}.log'
gh run list -R adhit-r/fairmind --workflow tests.yml --created 2026-10-31..2026-11-11 --limit 2000 \
  --json databaseId,headBranch,createdAt,conclusion > all_runs.json
python ../analysis/classify_ci_failures.py --runs failed_runs.csv --logs logs --all-runs all_runs.json
```

Needs `git` with `origin/main` fetched and an authenticated `gh`. `compute_metrics.py` writes `metrics.json`
(commits, AI co-author trailers, merged pull requests, test runs, failed jobs, releases, Scorecard),
`daily.csv` and `failed_runs.csv`. `classify_ci_failures.py` writes `ci_failures.csv` and
`ci_failures_summary.json`. GitHub keeps Actions logs for 90 days, so the logs step must run before early
February 2027; the committed CSVs hold the classification made on 10 November 2026.

All day boundaries are UTC. The Scorecard figures are whatever the API returns on the day you run it.
