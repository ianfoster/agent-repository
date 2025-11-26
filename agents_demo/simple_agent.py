# agents_demo/simple_academy_agent.py

from __future__ import annotations
from typing import Dict

from academy.agent import Agent, action  # from Academy


class SimpleDemoAgent(Agent):
    """
    Simple Academy-based demo agent.

    Exposes a single action `greet` that returns a greeting JSON blob.
    """

    @action
    async def greet(self, name: str = "world") -> Dict[str, str]:
        return {
            "greeting": f"Hello, {name}! (from {self.__class__.__name__})"
        }
