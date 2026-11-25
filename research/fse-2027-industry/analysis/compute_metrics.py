"""Recompute every number in the FSE 2027 industry paper from public sources.

Usage: python compute_metrics.py --start 2026-11-01 --end 2026-11-09 [--tz +05:30] [--out DIR]
Needs: git (run inside the repository, with origin/main fetched) and an authenticated `gh`.
"""
import argparse, collections, csv, json, re, subprocess, urllib.request
from datetime import datetime, timedelta, timezone

REPO = "adhit-r/fairmind"
AI_TRAILER = re.compile(r"^Co-Authored-By:.*(Claude|Copilot|GPT|Gemini|Codex)", re.I | re.M)


def sh(*args):
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def gh_json(*args):
    return json.loads(sh("gh", *args))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", default="2026-11-01")
    p.add_argument("--end", default="2026-11-09", help="inclusive")
    p.add_argument("--tz", default="+05:30", help="maintainer's local offset, used for day boundaries")
    p.add_argument("--branch", default="origin/main")
    p.add_argument("--out", default=".")
    a = p.parse_args()

    h, m = map(int, a.tz.lstrip("+-").split(":"))
    tz = timezone((-1 if a.tz.startswith("-") else 1) * timedelta(hours=h, minutes=m))
    start = datetime.fromisoformat(a.start).replace(tzinfo=tz)
    end = datetime.fromisoformat(a.end).replace(tzinfo=tz) + timedelta(days=1)
    days = [(start + timedelta(days=i)).date().isoformat() for i in range((end - start).days)]
    local_day = lambda iso: datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(tz).date().isoformat()

    # Commits: selected by committer date (when they landed on main), plotted by author date.
    log = sh("git", "log", a.branch, "--no-merges", f"--since={start.isoformat()}", f"--until={end.isoformat()}",
             "--format=%H%x1f%aI%x1f%cI%x1f%B%x1e")
    commits = [c.strip().split("\x1f") for c in log.split("\x1e") if c.strip()]
    ai = [c for c in commits if AI_TRAILER.search(c[3])]
    models = collections.Counter(
        m.group(1).strip() for c in ai for m in re.finditer(r"^Co-Authored-By:\s*([^<\n]+)", c[3], re.I | re.M))
    commits_by_day = collections.Counter(local_day(c[1]) for c in commits)
    earlier_author_date = sum(1 for c in commits if local_day(c[1]) < days[0])

    # Merged pull requests, by merge time.
    prs = gh_json("pr", "list", "-R", REPO, "--state", "merged", "--limit", "2000",
                  "--search", f"merged:{start.isoformat()}..{end.isoformat()}", "--json", "number,mergedAt")
    prs = [x for x in prs if start <= datetime.fromisoformat(x["mergedAt"].replace("Z", "+00:00")) < end]
    prs_by_day = collections.Counter(local_day(x["mergedAt"]) for x in prs)

    # Test workflow runs and the jobs that failed.
    runs = gh_json("run", "list", "-R", REPO, "--workflow", "tests.yml", "--limit", "2000",
                   "--created", f"{(start - timedelta(days=1)).date()}..{end.date()}",
                   "--json", "databaseId,conclusion,createdAt,headBranch,event,url")
    runs = [r for r in runs if start <= datetime.fromisoformat(r["createdAt"].replace("Z", "+00:00")) < end]
    outcomes = collections.Counter(r["conclusion"] or "in_progress" for r in runs)
    failed_jobs = collections.Counter()
    failed_rows = []
    for r in runs:
        if r["conclusion"] != "failure":
            continue
        jobs = gh_json("api", f"repos/{REPO}/actions/runs/{r['databaseId']}/jobs?per_page=100")["jobs"]
        bad = [j["name"] for j in jobs if j["conclusion"] == "failure"]
        failed_jobs.update(bad)
        failed_rows.append({**r, "failed_jobs": ";".join(bad)})

    releases = gh_json("api", f"repos/{REPO}/releases?per_page=100")
    releases = [{"tag": x["tag_name"], "published": x["published_at"],
                 "signed": any(s["name"].endswith((".sigstore.json", ".sigstore", ".intoto.jsonl")) for s in x["assets"])}
                for x in releases if x["published_at"] and start <= datetime.fromisoformat(x["published_at"].replace("Z", "+00:00")) < end]

    with urllib.request.urlopen(f"https://api.securityscorecards.dev/projects/github.com/{REPO}") as f:
        sc = json.load(f)

    result = {
        "window": {"start": a.start, "end_inclusive": a.end, "tz": a.tz, "branch": a.branch},
        "commits_non_merge": len(commits),
        "commits_ai_coauthored": len(ai),
        "commits_ai_share": round(len(ai) / len(commits), 3) if commits else None,
        "commits_author_date_before_window": earlier_author_date,
        "ai_coauthor_names": dict(models.most_common()),
        "merged_prs": len(prs),
        "merged_prs_per_day_min_max": [min(prs_by_day[d] for d in days), max(prs_by_day[d] for d in days)],
        "test_runs": dict(outcomes),
        "failed_runs_by_job": dict(failed_jobs.most_common()),
        "releases": releases,
        "scorecard": {"date": sc.get("date"), "score": sc.get("score"),
                      "checks": {c["name"]: c["score"] for c in sc.get("checks", [])}},
    }
    with open(f"{a.out}/metrics.json", "w") as f:
        json.dump(result, f, indent=1)
    with open(f"{a.out}/daily.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["date", "commits_by_author_date", "merged_prs"])
        for d in days:
            w.writerow([d, commits_by_day[d], prs_by_day[d]])
    with open(f"{a.out}/failed_runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["databaseId", "createdAt", "headBranch", "event", "failed_jobs", "url", "conclusion"])
        w.writeheader()
        w.writerows(failed_rows)
    print(json.dumps({k: v for k, v in result.items() if k != "scorecard"}, indent=1))


if __name__ == "__main__":
    main()
