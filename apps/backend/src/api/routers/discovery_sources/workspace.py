"""A chat workspace described by the person who runs it: ChatGPT Business or Team, or Claude Team. These
plans have no admin API, so the source holds what the admin told FairMind and re-reads it on each sync; the
review cadence says when the description is due another look.

config: workspace_name, plan, seats, owner, assistants ([{name, purpose, audience}], custom GPTs or projects),
apps (connectors it can reach), memory, history, review_days. token: none.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from . import asset, need

VENDORS = {"chatgpt_workspace": ("ChatGPT", "OpenAI", "custom GPT"), "claude_team": ("Claude", "Anthropic", "project")}
MAX_ASSISTANTS = 200


def _sync_for(kind: str):
    product, vendor, assistant_word = VENDORS[kind]

    async def sync(config: Dict[str, Any], token: Optional[str]) -> List[Dict[str, Any]]:
        name = need(config, "workspace_name", "Workspace name")
        try:
            seats = int(config.get("seats") or 0)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail="Seats must be a number") from None
        apps = [str(a) for a in (config.get("apps") or []) if str(a).strip()][:50]
        key = f"{kind}:{name.lower()}"
        found = [asset(
            key, f"{product} workspace: {name}", "ai_service",
            {
                "vendor": vendor, "plan": str(config.get("plan") or ""), "seats": seats, "owner": str(config.get("owner") or ""),
                "apps": apps, "memory": config.get("memory"), "history": config.get("history"),
                "review_days": config.get("review_days"), "described_by_admin": True, "signal": f"{product} workspace",
            },
            tier="medium" if apps else "low", stage="operate",
        )]
        for a in (config.get("assistants") or [])[:MAX_ASSISTANTS]:
            title = str((a or {}).get("name") or "").strip()
            if not title:
                continue
            found.append(asset(
                f"{key}:{title.lower()}", title, "llm_app",
                {"vendor": vendor, "workspace": name, "purpose": str(a.get("purpose") or ""), "audience": str(a.get("audience") or ""),
                 "kind_in_vendor": assistant_word, "described_by_admin": True, "signal": f"{product} {assistant_word}"},
                tier="medium" if a.get("audience") == "workspace" else "low", stage="operate",
            ))
        return found

    return sync


chatgpt_sync = _sync_for("chatgpt_workspace")
claude_team_sync = _sync_for("claude_team")
