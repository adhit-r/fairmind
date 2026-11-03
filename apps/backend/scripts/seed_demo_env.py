"""
Seed the public demo environment through the API, the same way a user would.

Synthetic data only, and only ever against the isolated demo database
(Neon branch "demo"). Registers the shared demo account, creates workspaces
and AI systems, and uploads generated decision logs so the backend computes
real fairness runs, gates and evidence from them. Each system's CSV carries a
deliberate, known bias pattern so the demo shows both passing and failing gates.

    DEMO_EMAIL=... DEMO_PASSWORD=... python scripts/seed_demo_env.py [base_url]

Reset: TRUNCATE the demo branch's public tables, then run this again.
"""

import csv
import io
import json
import os
import random
import sys
import urllib.error
import urllib.request
import uuid

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
GOV = f"{BASE}/api/v1/ai-governance"

WORKSPACES = {"lending": "Retail Lending", "people": "People and Customer Operations"}

# (workspace, name, owner, risk tier, stage, frameworks, CSV spec or None)
# CSV spec: attribute -> {group: approval-rate shift}; groups not listed get no shift.
SYSTEMS = [
    ("lending", "Retail credit underwriting", "Credit Risk ML", "high", "govern",
     ["RBI FREE-AI", "DPDP Act 2023", "EU AI Act"],
     {"base": 0.62, "shift": {"gender": {"female": -0.16, "non-binary": -0.12}}}),
    ("people", "Resume screening ranker", "Talent Acquisition", "high", "assess",
     ["EU AI Act", "NYC Local Law 144", "DPDP Act 2023"],
     {"base": 0.35, "shift": {"age_band": {"46-60": -0.15, "60+": -0.2}}}),
    ("lending", "Card fraud detection", "Fraud Analytics", "medium", "operate",
     ["RBI FREE-AI", "ISO/IEC 42001"],
     {"base": 0.9, "shift": {}}),
    ("lending", "Insurance claims triage", "Claims Operations", "medium", "remediate",
     ["IRDAI guidelines", "DPDP Act 2023"],
     {"base": 0.7, "shift": {"region": {"north-east": -0.09}}}),
    ("people", "Customer support assistant (LLM)", "Support Engineering", "low", "onboard",
     ["EU AI Act", "NIST AI RMF"],
     None),
]

ATTRIBUTES = {
    "gender": (["female", "male", "non-binary"], [0.47, 0.5, 0.03]),
    "age_band": (["18-30", "31-45", "46-60", "60+"], [0.3, 0.35, 0.25, 0.1]),
    "region": (["north", "south", "east", "west", "north-east"], [0.24, 0.24, 0.2, 0.24, 0.08]),
}


def call(method, url, token=None, body=None, files=None):
    headers = {"Accept": "application/json"}
    data = None
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if files is not None:
        boundary = uuid.uuid4().hex
        parts = []
        for key, value in (body or {}).items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{value}\r\n'.encode())
        for key, (filename, content) in files.items():
            parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                f"Content-Type: text/csv\r\n\r\n".encode() + content + b"\r\n"
            )
        data = b"".join(parts) + f"--{boundary}--\r\n".encode()
        headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
    elif body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")[:400]


def decision_log(spec, rng, rows=2000):
    """Synthetic decision log: outcome is the true label, prediction/score are the model's output."""
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["applicant_id", *ATTRIBUTES, "score", "prediction", "outcome"])
    for i in range(rows):
        groups = {a: rng.choices(vals, weights)[0] for a, (vals, weights) in ATTRIBUTES.items()}
        rate = spec["base"] + sum(spec["shift"].get(a, {}).get(g, 0.0) for a, g in groups.items())
        score = min(max(rng.gauss(rate, 0.18), 0.0), 1.0)
        prediction = int(score >= 0.5)
        # True label agrees with the model ~85% of the time, independent of group.
        outcome = prediction if rng.random() < 0.85 else 1 - prediction
        writer.writerow([f"A{i:05d}", *groups.values(), f"{score:.4f}", prediction, outcome])
    return out.getvalue().encode()


def require(status, payload, what):
    if status >= 300:
        sys.exit(f"{what} failed ({status}): {payload}")
    return payload


def main():
    email, password = os.environ["DEMO_EMAIL"], os.environ["DEMO_PASSWORD"]
    rng = random.Random(42)

    status, payload = call("POST", f"{BASE}/api/v1/auth/register", body={
        "email": email, "password": password, "name": "Demo Reviewer", "org_name": "Northwind Financial (demo)",
    })
    if status == 409:
        status, payload = call("POST", f"{BASE}/api/v1/auth/login", body={"email": email, "password": password})
    token = require(status, payload, "register/login")["access_token"]
    print(f"demo account ready ({'registered' if status == 201 else 'logged in'})")

    status, existing = call("GET", f"{GOV}/systems", token)
    if status < 300 and existing:
        sys.exit("demo org already has systems; reset the demo branch before reseeding")

    workspace_ids = {}
    for key, name in WORKSPACES.items():
        ws = require(*call("POST", f"{GOV}/workspaces", token, {"name": name, "owner": "Demo Reviewer"}), f"workspace {name}")
        workspace_ids[key] = ws["id"]

    for ws_key, name, owner, tier, stage, frameworks, spec in SYSTEMS:
        system = require(*call("POST", f"{GOV}/systems", token, {
            "workspace_id": workspace_ids[ws_key], "name": name, "owner": owner,
            "risk_tier": tier, "lifecycle_stage": stage,
            "metadata": {"created_from": "demo-seed", "synthetic": True, "compliance_frameworks": frameworks},
        }), f"system {name}")
        line = f"system {name}: {tier}/{stage}"
        if spec:
            attrs = ",".join(ATTRIBUTES)
            status, run = call("POST", f"{GOV}/systems/{system['id']}/fairness-runs", token,
                               {"outcome": "outcome", "prediction": "prediction", "score": "score",
                                "attributes": attrs, "favorable_label": "1"},
                               files={"file": (f"{system['id']}-baseline.csv", decision_log(spec, rng))})
            line += f", fairness run {status}"
            if stage == "operate":
                status, _ = call("POST", f"{GOV}/systems/{system['id']}/monitoring-runs", token,
                                 {"prediction": "prediction", "score": "score", "attributes": attrs, "favorable_label": "1"},
                                 files={"file": (f"{system['id']}-production.csv", decision_log(spec, rng, rows=1500))})
                line += f", monitoring run {status}"
        if tier == "high":
            status, _ = call("POST", f"{GOV}/approval/system/{system['id']}/request", token, {})
            line += f", approval request {status}"
        print(line)


if __name__ == "__main__":
    main()
