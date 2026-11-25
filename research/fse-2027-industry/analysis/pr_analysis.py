"""Pull-request level analysis for the FSE 2027 industry paper.

Usage: python pr_analysis.py --start 2026-11-01 --end 2026-11-09 --rule-at 2026-11-07T19:14:40Z \
           [--ci-failures ci_failures.csv] [--cache DIR] [--out DIR]
Needs an authenticated `gh`. Fetches every pull request merged in the window with its commits, reviews,
files and the check runs on its head commit (cached as JSON), then writes prs.csv and pr_summary.json.
"""
import argparse, collections, csv, json, os, re, statistics, subprocess, time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

REPO = "adhit-r/fairmind"
# The checks the branch ruleset made required at --rule-at.
REQUIRED = {"backend", "frontend", "cli", "sdk", "mcp", "e2e-tests", "e2e-smoke-tests", "dependency-review"}
T = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def gh(*args, tries=4):
    for i in range(tries):  # the API fails transiently under parallel load
        r = subprocess.run(["gh", *args], capture_output=True, text=True)
        if r.returncode == 0:
            return r.stdout
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"gh {' '.join(args)} failed: {r.stderr[:200]}")


def area(path):
    if path.startswith((".github/", "tooling/")): return "CI, workflows, tooling"
    if path.startswith("apps/backend/"): return "backend"
    if path.startswith("apps/frontend/"): return "frontend"
    if path.startswith(("apps/website/", "apps/docs/")): return "website, docs site"
    if re.match(r"apps/(sdk|cli|mcp)|packages/|sdk/", path): return "SDK, CLI, MCP"
    if path.startswith(("research/", "paper/")): return "research, papers"
    if path.startswith("docs/") or path.endswith(".md"): return "documentation"
    return "other"


def fetch(n, cache):
    f = f"{cache}/pr_{n}.json"
    if os.path.exists(f):
        return json.load(open(f))
    d = json.loads(gh("pr", "view", str(n), "-R", REPO, "--json",
                      "number,title,createdAt,mergedAt,additions,deletions,changedFiles,headRefName,headRefOid,"
                      "author,mergedBy,reviews,files,commits,comments"))
    d["commits"] = [{"oid": c["oid"], "date": c["committedDate"], "msg": c["messageHeadline"]} for c in d["commits"]]
    d["comments"] = [c["author"]["login"] for c in d["comments"]]
    out = gh("api", "--paginate", f"repos/{REPO}/commits/{d['headRefOid']}/check-runs?per_page=100",
             "-q", ".check_runs[]|{name,conclusion,started_at,completed_at}")
    d["checks"] = [json.loads(l) for l in out.splitlines() if l.strip()]
    json.dump(d, open(f, "w"))
    return d


def merge_state(p):
    """State of the REQUIRED checks on the head commit at the moment of merge."""
    m = T(p["mergedAt"])
    cr = [c for c in p["checks"] if c["name"] in REQUIRED and T(c["started_at"]) and T(c["started_at"]) < m]
    if not cr:
        return "none", [], []
    pend = [c for c in cr if not T(c["completed_at"]) or T(c["completed_at"]) > m]
    fail = [c for c in cr if T(c["completed_at"]) and T(c["completed_at"]) <= m and c["conclusion"] == "failure"]
    later = [c["name"] for c in pend if c["conclusion"] == "failure"]
    return ("failing" if fail else "pending" if pend else "passed"), later, [c["name"] for c in fail]


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--start", default="2026-11-01"); a.add_argument("--end", default="2026-11-09")
    a.add_argument("--rule-at", default="2026-11-07T19:14:40Z", help="when status checks became required")
    a.add_argument("--ci-failures", help="ci_failures.csv from classify_ci_failures.py, to explain bypassed failures")
    a.add_argument("--cache", default="cache"); a.add_argument("--out", default=".")
    a = a.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    nums = json.loads(gh("pr", "list", "-R", REPO, "--state", "merged", "--limit", "2000", "--search",
                         f"merged:{a.start}T00:00:00Z..{a.end}T23:59:59Z", "--json", "number"))
    with ThreadPoolExecutor(4) as ex:
        prs = sorted(ex.map(lambda x: fetch(x["number"], a.cache), nums), key=lambda p: p["number"])
    rule = T(a.rule_at)
    minutes = lambda p: (T(p["mergedAt"]) - T(p["createdAt"])).total_seconds() / 60
    q = lambda v, x: sorted(v)[min(len(v) - 1, int(len(v) * x))]

    for p in prs:
        c = collections.Counter()
        for f in p["files"]:
            c[area(f["path"])] += f["additions"] + f["deletions"] + 1
        p["area"] = c.most_common(1)[0][0] if c else "other"
        p["state"], p["later_failed"], p["failed_before"] = merge_state(p)
        p["era"] = "after" if T(p["mergedAt"]) >= rule else "before"
        p["approvals"] = sum(r["state"] == "APPROVED" for r in p["reviews"])
        p["late_commits"] = [c for c in p["commits"] if T(c["date"]) > T(p["createdAt"])]
        p["touches_tested_code"] = any(f["path"].startswith(("apps/backend/", "research/")) for f in p["files"])

    gate = {era: {**collections.Counter(p["state"] for p in prs if p["era"] == era),
                  "merged": sum(p["era"] == era for p in prs),
                  "pending_then_failed": sum(1 for p in prs if p["era"] == era and p["state"] == "pending" and p["later_failed"])}
            for era in ("before", "after")}
    backend = [(T(c["completed_at"]) - T(c["started_at"])).total_seconds() / 60 for p in prs for c in p["checks"]
               if c["name"] == "backend" and c["conclusion"] == "success" and c["completed_at"]]
    ttm = [minutes(p) for p in prs]
    bypassed = [p for p in prs if p["later_failed"] and p["state"] == "pending" or p["state"] == "failing"]
    why = collections.Counter()
    if a.ci_failures:  # explain each bypassed backend failure by the classified cause of the run on that commit
        runs = json.loads(gh("run", "list", "-R", REPO, "--workflow", "tests.yml", "--limit", "2000",
                             "--json", "databaseId,headSha"))
        cause = {r["run"]: r["cause"] for r in csv.DictReader(open(a.ci_failures))}
        by_sha = collections.defaultdict(list)
        for r in runs:
            if str(r["databaseId"]) in cause:
                by_sha[r["headSha"]].append(cause[str(r["databaseId"])])
        for p in bypassed:
            names = set(p["later_failed"] or p["failed_before"])
            why[(by_sha.get(p["headRefOid"]) or ["unclassified"])[0] if "backend" in names else "not the backend job"] += 1

    pending = [p for p in prs if p["state"] == "pending"]
    summary = {
        "merged_prs": len(prs),
        "opened_by": dict(collections.Counter(p["author"]["login"] for p in prs)),
        "merged_by": dict(collections.Counter((p["mergedBy"] or {}).get("login") for p in prs)),
        "approving_reviews_per_pr": dict(collections.Counter(p["approvals"] for p in prs)),
        "review_events_by_author": dict(collections.Counter(r["author"]["login"] + ":" + r["state"] for p in prs for r in p["reviews"])),
        "comments_by_author": dict(collections.Counter(c for p in prs for c in p["comments"])),
        "lines_added": sum(p["additions"] for p in prs), "lines_deleted": sum(p["deletions"] for p in prs),
        "additions_median": statistics.median(p["additions"] for p in prs), "additions_p90": q([p["additions"] for p in prs], .9),
        "minutes_to_merge": {"median": round(statistics.median(ttm), 1), "p25": round(q(ttm, .25), 1),
                             "under_5": sum(x < 5 for x in ttm)},
        "backend_job_minutes_median": round(statistics.median(backend), 1),
        "merged_faster_than_backend_job": sum(x <= statistics.median(backend) for x in ttm),
        "prs_by_area": dict(collections.Counter(p["area"] for p in prs).most_common()),
        "gate": gate,
        "merged_with_failed_or_soon_failing_check": len(bypassed),
        "bypassed_failure_causes": dict(why),
        "merged_while_running": len(pending),
        "merged_while_running_not_touching_tested_code": sum(not p["touches_tested_code"] for p in pending),
        "prs_with_commits_after_open": sum(bool(p["late_commits"]) for p in prs),
        "commits_after_open": sum(len(p["late_commits"]) for p in prs),
    }
    json.dump(summary, open(f"{a.out}/pr_summary.json", "w"), indent=1)
    with open(f"{a.out}/prs.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pr", "created", "merged", "minutes_to_merge", "additions", "deletions", "files", "commits", "area",
                    "approving_reviews", "era", "check_state_at_merge", "running_check_later_failed"])
        for p in prs:
            w.writerow([p["number"], p["createdAt"], p["mergedAt"], round(minutes(p), 1), p["additions"], p["deletions"],
                        p["changedFiles"], len(p["commits"]), p["area"], p["approvals"], p["era"], p["state"],
                        ";".join(p["later_failed"])])
    with open(f"{a.out}/commits_after_open.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pr", "commit", "headline"])
        for p in prs:
            for c in p["late_commits"]:
                w.writerow([p["number"], c["oid"][:10], c["msg"]])
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
