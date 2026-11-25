"""How FairMind calls an AI system under test, for behaviour tests.

GET    /ai-systems/{id}/target        the saved connection; the auth value never comes back, only a hint
PUT    /ai-systems/{id}/target        save it (a blank auth value keeps the stored one)
DELETE /ai-systems/{id}/target
POST   /ai-systems/{id}/target/test   send one prompt to the saved connection and record whether it answered

Two kinds of target: an OpenAI-compatible Chat Completions endpoint, or a plain HTTP endpoint that takes
a JSON body (a template with {{prompt}} in it) and answers JSON (the answer read at a dot path). The
endpoint goes through the same public-https guard as the organisation's own model, and the auth value is
encrypted the same way its key is. Mounted under /api/v1/packs beside the packs router.

A target saved with via=runner is called by the FairMind CLI inside the customer's network
(`fairmind eval run --live --local`), never by this server: its URL may be private, no auth value is
stored (the runner holds it), and ask() refuses it.
"""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.routes import llm
from api.routes.ai_governance import _ensure_tables, _load_json_value, _utc_now_iso
from api.routes.packs import _manager, _member
from database.connection import get_db
from src.application.services.governance_assurance_service import OrgMembership

logger = logging.getLogger(__name__)
router = APIRouter()

TIMEOUT_S = 60  # runs are background jobs, so this is per call, not per request
MAX_ANSWER_BYTES = 1024 * 1024
TEST_PROMPT = "This is a connection check from FairMind. Reply with one short sentence."


class TargetError(Exception):
    """The system under test could not be called; the message never carries the auth value."""


class Unreachable(TargetError):
    pass


class TimedOut(TargetError):
    pass


class AuthRejected(TargetError):
    pass


class BadStatus(TargetError):
    pass


class BadAnswer(TargetError):
    pass


# What the connection test tells the person; the exception's own detail goes to the server log.
FIXES = (
    (TimedOut, f"The system did not answer within {TIMEOUT_S} seconds"),
    (Unreachable, "Could not reach the system. Check the URL"),
    (AuthRejected, "The system rejected the auth value. Enter it again and save"),
    (BadStatus, "The system answered with an error status. Check the URL, the model name and the request body"),
    (BadAnswer, "The system's answer could not be read. Check that it returns JSON and that the answer path is right"),
    (llm.LLMError, "The endpoint must be a public https address that resolves"),
)


def _fix(e: Exception) -> str:
    return next((message for kind, message in FIXES if isinstance(e, kind)), "Could not call the system. Check the connection settings")


@dataclass
class Target:
    kind: str
    url: str
    fields: Dict[str, str]
    auth: Optional[str]

    @property
    def system_prompt(self) -> str:
        return self.fields.get("systemPrompt", "")

    @property
    def intended_use(self) -> str:
        return self.fields.get("intendedUse", "")

    @property
    def via_runner(self) -> bool:
        return self.fields.get("via") == "runner"


def runner_command(evaluation_id: str, system_id: str) -> str:
    return f"fairmind eval run {evaluation_id} --system {system_id} --live --local"


def _fill(template: Any, prompt: str) -> Any:
    if isinstance(template, str):
        return template.replace("{{prompt}}", prompt)
    if isinstance(template, list):
        return [_fill(v, prompt) for v in template]
    if isinstance(template, dict):
        return {k: _fill(v, prompt) for k, v in template.items()}
    return template


def _at(data: Any, path: str) -> Any:
    for part in [p for p in path.split(".") if p]:
        if isinstance(data, list) and part.isdigit() and int(part) < len(data):
            data = data[int(part)]
        elif isinstance(data, dict) and part in data:
            data = data[part]
        else:
            raise BadAnswer(f"The answer has nothing at {path}")
    return data


async def ask(target: Target, prompt: str, attempts: int = 1) -> str:
    """One prompt to the system under test and its answer as text; attempts > 1 retries rate limits and gateway errors."""
    if target.via_runner:
        raise Unreachable("This system is called by your runner inside your network, not by FairMind")
    url = llm._public_https(target.url, "Endpoint")  # again at call time: DNS can change after save
    headers = {}
    if target.kind == "openai":
        if target.auth:
            headers["Authorization"] = f"Bearer {target.auth}"
        messages = [{"role": "system", "content": target.system_prompt}] if target.system_prompt else []
        body: Any = {"model": target.fields.get("model", ""), "messages": messages + [{"role": "user", "content": prompt}]}
        url = f"{url}/chat/completions"
    else:
        if target.auth:
            headers[target.fields.get("authHeader") or "Authorization"] = target.auth
        body = _fill(json.loads(target.fields["requestTemplate"]), prompt)
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S, headers=headers, follow_redirects=False) as client:
            # a chat model is asked at temperature 0 where it accepts it, so a run can be repeated
            resp = await (llm.post_at_zero(client, url, attempts, body) if target.kind == "openai" else llm.post_with_retry(client, url, attempts, json=body))
    except httpx.TimeoutException:
        raise TimedOut("The system did not answer in time")
    except httpx.HTTPError:
        raise Unreachable("Could not reach the system")
    if resp.status_code in (401, 403):
        raise AuthRejected(f"The system rejected the auth value ({resp.status_code})")
    if resp.status_code >= 400:
        raise BadStatus(f"The system responded {resp.status_code}")
    if len(resp.content) > MAX_ANSWER_BYTES:
        raise BadAnswer("The answer is over 1 MB")
    try:
        data = resp.json()
    except ValueError:
        if target.kind == "http" and not target.fields.get("responsePath"):
            return resp.text
        raise BadAnswer("The system did not answer with JSON")
    if target.kind == "openai":
        try:
            answer = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            raise BadAnswer("The system returned no message")
    else:
        answer = _at(data, target.fields.get("responsePath", ""))
    return answer if isinstance(answer, str) else json.dumps(answer)


# --- storage ------------------------------------------------------------------


class TargetBody(BaseModel):
    kind: Literal["openai", "http"]
    via: Literal["fairmind", "runner"] = "fairmind"
    url: str = Field(min_length=1, max_length=500)
    model: str = Field(default="", max_length=200)
    systemPrompt: str = Field(default="", max_length=20000)
    intendedUse: str = Field(default="", max_length=4000)
    authHeader: str = Field(default="", max_length=100)
    authValue: Optional[str] = Field(default=None, max_length=4000)  # omitted on save: keep the stored value
    requestTemplate: str = Field(default="", max_length=20000)
    responsePath: str = Field(default="", max_length=200)


def _system_or_404(db: Session, org_id: str, system_id: str) -> None:
    row = db.execute(text("SELECT org_id FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).fetchone()
    if not row or str(row[0]) != org_id:
        raise HTTPException(status_code=404, detail="AI system not found")


def _row(db: Session, system_id: str):
    return db.execute(text("SELECT * FROM governance_ai_system_targets WHERE system_id = :id"), {"id": system_id}).mappings().fetchone()


def _json(row) -> Optional[dict]:
    if not row:
        return None
    return {
        "kind": row["kind"],
        "url": row["url"],
        **json.loads(row["fields_json"] or "{}"),
        "hasAuth": bool(row["auth_enc"]),
        "authHint": row["auth_hint"],
        "authReadable": not row["auth_enc"] or llm.decrypt(row["auth_enc"]) is not None,
        "testedOk": None if row["tested_ok"] is None else bool(row["tested_ok"]),
        "testedAt": row["tested_at"],
        "testMessage": row["test_message"],
        "updatedAt": row["updated_at"],
    }


def stored_target(db: Session, org_id: str, system_id: str) -> Target:
    """The saved connection, ready to call; 409 with what to fix when there is none or it cannot be used."""
    row = _row(db, system_id)
    if not row or row["org_id"] != org_id:
        raise HTTPException(status_code=409, detail="Set how FairMind calls this AI system first, on the system's page")
    auth = llm.decrypt(row["auth_enc"])
    if row["auth_enc"] and auth is None:
        raise HTTPException(status_code=409, detail="The stored auth value for this system can no longer be read; enter it again")
    fields = json.loads(row["fields_json"] or "{}")
    if not fields.get("intendedUse"):  # the purpose a person gave when classifying the system, when the connection has none
        meta = db.execute(text("SELECT metadata_json FROM governance_ai_systems WHERE id = :id"), {"id": system_id}).scalar()
        purpose = ((_load_json_value(meta, {}).get("applicability") or {}).get("answers") or {}).get("intendedPurpose")
        fields["intendedUse"] = (purpose or "").strip()
    return Target(row["kind"], row["url"], fields, auth)


def _fields(body: TargetBody) -> Dict[str, str]:
    fields = {"systemPrompt": body.systemPrompt.strip(), "intendedUse": body.intendedUse.strip()}
    if body.via == "runner":
        fields["via"] = "runner"
    if body.kind == "openai":
        if not body.model.strip():
            raise HTTPException(status_code=422, detail="Enter the model name the endpoint expects")
        fields["model"] = body.model.strip()
        return fields
    try:
        template = json.loads(body.requestTemplate)
    except ValueError:
        raise HTTPException(status_code=422, detail="The request body template must be valid JSON")
    if "{{prompt}}" not in json.dumps(template):
        raise HTTPException(status_code=422, detail="Put {{prompt}} in the request body template where the prompt goes")
    fields.update({"requestTemplate": json.dumps(template), "responsePath": body.responsePath.strip(), "authHeader": body.authHeader.strip()})
    return fields


@router.get("/ai-systems/{system_id}/target")
def get_target(system_id: str, m: OrgMembership = Depends(_member), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    return {"target": _json(_row(db, system_id))}


@router.put("/ai-systems/{system_id}/target")
def save_target(system_id: str, body: TargetBody, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    if body.via == "runner":
        # Never fetched by this server, so a private address is fine; only the runner calls it.
        url = body.url.strip().rstrip("/")
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise HTTPException(status_code=422, detail="Endpoint must be an http:// or https:// URL")
    else:
        try:
            url = llm._public_https(body.url, "Endpoint")
        except llm.LLMError as e:
            raise HTTPException(status_code=422, detail=str(e))
    fields = _fields(body)
    stored = _row(db, system_id)
    runner = body.via == "runner"
    auth = None if runner else (body.authValue or "").strip() or None  # a runner keeps its own auth value
    keep = not runner and auth is None and stored is not None and stored["kind"] == body.kind
    db.execute(
        text(
            "INSERT INTO governance_ai_system_targets (system_id, org_id, kind, url, fields_json, auth_enc, auth_hint, "
            "tested_ok, tested_at, test_message, updated_by, updated_at) VALUES (:id, :org, :kind, :url, :fields, :auth, :hint, "
            "NULL, NULL, NULL, :by, :now) ON CONFLICT (system_id) DO UPDATE SET kind = excluded.kind, url = excluded.url, "
            "fields_json = excluded.fields_json, auth_enc = excluded.auth_enc, auth_hint = excluded.auth_hint, tested_ok = NULL, "
            "tested_at = NULL, test_message = NULL, updated_by = excluded.updated_by, updated_at = excluded.updated_at"
        ),
        {
            "id": system_id,
            "org": m.org_id,
            "kind": body.kind,
            "url": url,
            "fields": json.dumps(fields, sort_keys=True),
            "auth": stored["auth_enc"] if keep else (llm.encrypt(auth) if auth else None),
            "hint": stored["auth_hint"] if keep else (llm.key_hint(auth) if auth else None),
            "by": m.user_id,
            "now": _utc_now_iso(),
        },
    )
    db.commit()
    return {"target": _json(_row(db, system_id))}


@router.delete("/ai-systems/{system_id}/target")
def delete_target(system_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    db.execute(text("DELETE FROM governance_ai_system_targets WHERE system_id = :id"), {"id": system_id})
    db.commit()
    return {"target": None}


@router.post("/ai-systems/{system_id}/target/test")
async def test_target(system_id: str, m: OrgMembership = Depends(_manager), db: Session = Depends(get_db)):
    _ensure_tables(db)
    _system_or_404(db, m.org_id, system_id)
    target = stored_target(db, m.org_id, system_id)
    if target.via_runner:
        raise HTTPException(status_code=409, detail="FairMind cannot reach this system; your runner calls it during a run: "
                            + runner_command("<evaluation>", system_id))
    db.rollback()  # hold no transaction open while the system answers
    started = time.monotonic()
    try:
        answer = await ask(target, TEST_PROMPT)
        ok, message = True, "The system answered"
    except (TargetError, llm.LLMError) as e:
        logger.info("connection test for AI system %s failed: %s", system_id, e)
        answer, ok, message = "", False, _fix(e)
    db.execute(
        text("UPDATE governance_ai_system_targets SET tested_ok = :ok, tested_at = :now, test_message = :msg WHERE system_id = :id"),
        {"ok": ok, "now": _utc_now_iso(), "msg": message[:300], "id": system_id},
    )
    db.commit()
    return {"ok": ok, "message": message, "answer": answer[:300], "latencyMs": round((time.monotonic() - started) * 1000) if ok else None}
