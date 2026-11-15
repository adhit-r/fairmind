"""Known third-party AI services: how they show up as a hostname in proxy logs and as an
application name in a sign-in provider. Static reference data, extended as vendors appear.

category: chat | api | dev | media | meeting | writing | platform
"""

from __future__ import annotations

import re
from typing import Dict, List, NamedTuple, Optional


class Service(NamedTuple):
    key: str
    label: str
    vendor: str
    category: str
    domains: tuple
    app_name: str  # regex matched against a sign-in provider's application name


SERVICES: List[Service] = [
    Service("azure_openai", "Azure OpenAI", "Microsoft", "api", ("openai.azure.com", "services.ai.azure.com", "cognitiveservices.azure.com"), r"\bazure\s+open\s?ai\b"),
    Service("chatgpt", "ChatGPT", "OpenAI", "chat", ("chatgpt.com", "chat.openai.com", "oaiusercontent.com"), r"\bchat\s?gpt\b"),
    Service("openai_api", "OpenAI API", "OpenAI", "api", ("api.openai.com",), r"\bopen\s?ai\b"),
    Service("claude", "Claude", "Anthropic", "chat", ("claude.ai", "claudeusercontent.com"), r"\bclaude\b"),
    Service("anthropic_api", "Anthropic API", "Anthropic", "api", ("api.anthropic.com", "console.anthropic.com"), r"\banthropic\b"),
    Service("gemini", "Gemini", "Google", "chat", ("gemini.google.com", "bard.google.com", "aistudio.google.com"), r"\bgemini\b"),
    Service("gemini_api", "Gemini API", "Google", "api", ("generativelanguage.googleapis.com",), r"(?!)"),
    Service("vertex_api", "Vertex AI API", "Google", "api", ("aiplatform.googleapis.com",), r"\bvertex\s?ai\b"),
    Service("microsoft_copilot", "Microsoft Copilot", "Microsoft", "chat", ("copilot.microsoft.com", "copilot.cloud.microsoft"), r"\bmicrosoft\s+(365\s+)?copilot\b"),
    Service("github_copilot", "GitHub Copilot", "GitHub", "dev", ("githubcopilot.com", "copilot-proxy.githubusercontent.com"), r"\bgithub\s+copilot\b"),
    Service("cursor", "Cursor", "Anysphere", "dev", ("cursor.com", "cursor.sh"), r"^cursor\b|\bcursor\s+(ai|editor|ide)\b"),
    Service("windsurf", "Windsurf", "Windsurf", "dev", ("windsurf.com", "codeium.com"), r"\b(windsurf|codeium)\b"),
    Service("tabnine", "Tabnine", "Tabnine", "dev", ("tabnine.com",), r"\btabnine\b"),
    Service("replit", "Replit", "Replit", "dev", ("replit.com",), r"\breplit\b"),
    Service("lovable", "Lovable", "Lovable", "dev", ("lovable.dev",), r"\blovable\b"),
    Service("v0", "v0", "Vercel", "dev", ("v0.dev", "v0.app"), r"^v0\b"),
    Service("bolt", "Bolt", "StackBlitz", "dev", ("bolt.new",), r"^bolt(\.new)?$"),
    Service("perplexity", "Perplexity", "Perplexity", "chat", ("perplexity.ai",), r"\bperplexity\b"),
    Service("mistral", "Mistral Le Chat", "Mistral AI", "chat", ("chat.mistral.ai", "console.mistral.ai"), r"\bmistral\b"),
    Service("mistral_api", "Mistral API", "Mistral AI", "api", ("api.mistral.ai",), r"(?!)"),
    Service("cohere", "Cohere", "Cohere", "api", ("cohere.com", "cohere.ai"), r"\bcohere\b"),
    Service("deepseek", "DeepSeek", "DeepSeek", "chat", ("deepseek.com",), r"\bdeepseek\b"),
    Service("grok", "Grok", "xAI", "chat", ("grok.com", "x.ai"), r"\bgrok\b|\bx\.?ai\b"),
    Service("meta_ai", "Meta AI", "Meta", "chat", ("meta.ai",), r"\bmeta\s+ai\b"),
    Service("poe", "Poe", "Quora", "chat", ("poe.com",), r"^poe$"),
    Service("character_ai", "Character.AI", "Character.AI", "chat", ("character.ai",), r"\bcharacter\.?ai\b"),
    Service("huggingface", "Hugging Face", "Hugging Face", "platform", ("huggingface.co", "hf.co"), r"\bhugging\s?face\b"),
    Service("groq", "Groq", "Groq", "api", ("groq.com",), r"\bgroq\b"),
    Service("together", "Together AI", "Together AI", "api", ("together.ai", "together.xyz"), r"\btogether\s+ai\b"),
    Service("fireworks", "Fireworks AI", "Fireworks AI", "api", ("fireworks.ai",), r"\bfireworks\s+ai\b"),
    Service("replicate", "Replicate", "Replicate", "api", ("replicate.com",), r"\breplicate\b"),
    Service("openrouter", "OpenRouter", "OpenRouter", "api", ("openrouter.ai",), r"\bopenrouter\b"),
    Service("sarvam", "Sarvam AI", "Sarvam AI", "api", ("sarvam.ai",), r"\bsarvam\b"),
    Service("krutrim", "Krutrim", "Ola", "chat", ("olakrutrim.com", "krutrim.com"), r"\bkrutrim\b"),
    Service("jasper", "Jasper", "Jasper", "writing", ("jasper.ai",), r"\bjasper(\s+ai)?$"),
    Service("copy_ai", "Copy.ai", "Copy.ai", "writing", ("copy.ai",), r"\bcopy\.ai\b"),
    Service("writer", "Writer", "Writer", "writing", ("writer.com",), r"^writer(\.com)?$"),
    Service("grammarly", "Grammarly", "Grammarly", "writing", ("grammarly.com", "grammarly.io"), r"\bgrammarly\b"),
    Service("gamma", "Gamma", "Gamma", "writing", ("gamma.app",), r"^gamma(\.app)?$"),
    Service("otter", "Otter.ai", "Otter.ai", "meeting", ("otter.ai",), r"\botter(\.ai)?\b"),
    Service("fireflies", "Fireflies.ai", "Fireflies.ai", "meeting", ("fireflies.ai",), r"\bfireflies\b"),
    Service("fathom", "Fathom", "Fathom", "meeting", ("fathom.video",), r"^fathom\b"),
    Service("midjourney", "Midjourney", "Midjourney", "media", ("midjourney.com",), r"\bmidjourney\b"),
    Service("runway", "Runway", "Runway", "media", ("runwayml.com",), r"\brunway(ml)?\b"),
    Service("elevenlabs", "ElevenLabs", "ElevenLabs", "media", ("elevenlabs.io",), r"\beleven\s?labs\b"),
    Service("synthesia", "Synthesia", "Synthesia", "media", ("synthesia.io",), r"\bsynthesia\b"),
]

_BY_DOMAIN: Dict[str, Service] = {d: s for s in SERVICES for d in s.domains}
_NAME_RES = [(re.compile(s.app_name, re.I), s) for s in SERVICES]


def by_host(host: str) -> Optional[Service]:
    """The service a hostname belongs to: exact domain or any subdomain of it."""
    host = host.lower().strip().rstrip(".")
    parts = host.split(".")
    for i in range(len(parts) - 1):
        hit = _BY_DOMAIN.get(".".join(parts[i:]))
        if hit:
            return hit
    return None


def by_app_name(name: str) -> Optional[Service]:
    """The service a sign-in provider's application name refers to."""
    name = (name or "").strip()
    if not name:
        return None
    for rx, s in _NAME_RES:
        if rx.search(name):
            return s
    return None


def asset_kind(s: Service) -> str:
    """Developer tools are AI-assisted development; raw API traffic means an internal app calls a model."""
    return {"dev": "ai_assisted_dev", "api": "llm_app"}.get(s.category, "ai_service")
