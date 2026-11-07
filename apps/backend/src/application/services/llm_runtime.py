"""Application-layer export of the LLM runtime for API routers.

Kept separate from api_boundary_dependencies so importing an LLM router does not
pull in the compliance, scheduler and report modules that file loads.
"""

from src.infrastructure.llm import grok_cli

__all__ = ["grok_cli"]
