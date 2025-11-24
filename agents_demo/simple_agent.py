# examples/agents_demo/agents_demo/simple_agent.py

from __future__ import annotations
from typing import Any, Dict


class SimpleDemoAgent:
    """
    Example agent implementation for local runs.

    Contract:
      - constructed with no arguments
      - exposes run(**inputs) -> dict
    """

    def run(self, **inputs: Any) -> Dict[str, Any]:
        # Just echo inputs and add a message.
        return {
            "received_inputs": inputs,
            "message": "Hello from SimpleDemoAgent running on your laptop!",
        }
