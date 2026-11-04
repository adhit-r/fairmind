"""Engines that read prompts, configuration and logs: system prompts, secrets, model files, tools, MCP, agents, cost and logs."""

from typing import List

from .common import Engine

ENGINES: List[Engine] = []
