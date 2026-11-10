"""Dependabot and code-scanning alert counts for the window. Needs `gh` with access to the repository's alerts.

Usage: python security_alerts.py --start 2026-11-01 --end 2026-11-09 > alerts_summary.json
"""
import argparse, collections, json, subprocess

REPO = "adhit-r/fairmind"


def rows(path, jq):
    out = subprocess.run(["gh", "api", "--paginate", f"repos/{REPO}/{path}", "-q", jq], check=True, capture_output=True, text=True).stdout
    return [json.loads(l) for l in out.splitlines() if l.strip()]


def main():
    a = argparse.ArgumentParser(); a.add_argument("--start", default="2026-11-01"); a.add_argument("--end", default="2026-11-09")
    a = a.parse_args()
    inw = lambda d: bool(d) and a.start <= d[:10] <= a.end
    dep = rows("dependabot/alerts?per_page=100", ".[]|{created:.created_at,closed:(.fixed_at // .dismissed_at),state,severity:.security_advisory.severity}")
    open_at_start = [r for r in dep if r["created"][:10] < a.start and (not r["closed"] or r["closed"][:10] >= a.start)]
    cs = rows("code-scanning/alerts?per_page=100", ".[]|{created:.created_at,closed:(.fixed_at // .dismissed_at),state,tool:.tool.name,severity:(.rule.security_severity_level // .rule.severity)}")
    raised = [r for r in cs if inw(r["created"])]
    print(json.dumps({
        "dependabot": {"open_at_start": len(open_at_start),
                       "open_at_start_by_severity": dict(collections.Counter(r["severity"] for r in open_at_start)),
                       "of_those_closed_in_window": sum(inw(r["closed"]) for r in open_at_start),
                       "last_closed": max((r["closed"] or "")[:10] for r in open_at_start) if open_at_start else None,
                       "opened_in_window": sum(inw(r["created"]) for r in dep)},
        "code_scanning": {"raised_in_window": len(raised),
                          "raised_by_tool_and_state": dict(collections.Counter(f"{r['tool']}:{r['state']}" for r in raised)),
                          "raised_high_by_tool": dict(collections.Counter(r["tool"] for r in raised if r["severity"] == "high")),
                          "older_alerts_closed_in_window": sum(1 for r in cs if r["created"][:10] < a.start and inw(r["closed"]))},
    }, indent=1))


if __name__ == "__main__":
    main()
