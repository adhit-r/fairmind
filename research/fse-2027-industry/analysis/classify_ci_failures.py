"""Classify the failed test-workflow runs by root cause from their failed-job logs.

Usage: python classify_ci_failures.py --runs failed_runs.csv --logs LOGDIR --all-runs all_runs.json --out DIR
failed_runs.csv comes from compute_metrics.py; LOGDIR holds `gh run view <id> --log-failed` output as <id>.log;
all_runs.json is `gh run list --workflow tests.yml --json databaseId,headBranch,createdAt,conclusion`.
Signatures were written after reading the logs; each maps a log pattern to a cause and whether the failure
was caused by the change under test.
"""
import argparse, csv, json, re, statistics, collections

# (cause, caused_by_change_under_test, pattern). First matching non-flaky signature wins; flaky ones last.
SIGS = [
    ("dependency upgrade broke an API", True, r"_IncludedRouter' object has no attribute 'path'"),
    ("dependency or environment", True, r"No module named 'psycopg'"),
    ("type error", True, r"error TS\d+"),
    ("design-rule ratchet", True, r"Frontend design rule counts changed"),
    ("break on main: SQLite-only SQL", False, r"no such function: right"),
    ("break on main: changed golden values", False, r"P01: confidence_score expected"),
    ("regression in the change", True, r"FAILED tests/(test_evaluation_worker_job_lifecycle|test_gate_explain|test_fairness_runs)"),
    ("frontend unit test", True, r"^frontend\t.*name: 'AssertionError'"),
    ("flaky: sandbox OOM classification", False, r"FAILED tests/test_sandbox_docker.py::test_memory_limit"),
    ("flaky: concurrency timeout", False, r"FAILED tests/test_owner_decision_override_postgres.py"),
    ("flaky: evidence revalidation", False, r"FAILED tests/test_verified_evidence_admission_postgres.py"),
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs"); p.add_argument("--logs"); p.add_argument("--all-runs"); p.add_argument("--out", default=".")
    a = p.parse_args()
    failed = list(csv.DictReader(open(a.runs)))
    allruns = sorted(json.load(open(a.all_runs)), key=lambda r: r["createdAt"])
    rows = []
    for r in failed:
        # Only failure lines: full logs also list passing tests by name.
        log = "\n".join(l for l in open(f"{a.logs}/{r['databaseId']}.log").read().splitlines()
                         if re.search(r"FAILED |Error|error|expected|counts changed", l))
        hits = [(c, own) for c, own, pat in SIGS if re.search(pat, log, re.M)]
        cause, own = hits[0] if hits else ("run-level failure, no failed job log", False)
        later = [x for x in allruns if x["headBranch"] == r["headBranch"] and x["createdAt"] > r["createdAt"]]
        n = next((i + 1 for i, x in enumerate(later) if x["conclusion"] == "success"), None)
        rows.append({"run": r["databaseId"], "created": r["createdAt"], "branch": r["headBranch"], "event": r["event"],
                     "failed_jobs": r["failed_jobs"], "cause": cause, "caused_by_change": own,
                     "also": ";".join(c for c, _ in hits[1:]), "runs_to_green": n if n else "", "url": r["url"]})
    with open(f"{a.out}/ci_failures.csv", "w", newline="") as f:
        w = csv.DictWriter(f, rows[0].keys()); w.writeheader(); w.writerows(rows)
    by = collections.defaultdict(list)
    for x in rows:
        by[x["cause"]].append(x)
    summary = [{"cause": c, "runs": len(v), "caused_by_change": v[0]["caused_by_change"],
                "median_runs_to_green": statistics.median([x["runs_to_green"] for x in v if x["runs_to_green"]] or [0])}
               for c, v in sorted(by.items(), key=lambda kv: -len(kv[1]))]
    json.dump(summary, open(f"{a.out}/ci_failures_summary.json", "w"), indent=1)
    for s in summary:
        print(f"{s['runs']:3d}  own={str(s['caused_by_change']):5s}  median_to_green={s['median_runs_to_green']}  {s['cause']}")
    print("caused by change under test:", sum(x["caused_by_change"] for x in rows), "of", len(rows))


if __name__ == "__main__":
    main()
