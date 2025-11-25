# agents_demo/stats_agent.py
from __future__ import annotations
from typing import Any, Dict, List
import statistics

class StatsDemoAgent:
    """Demo agent that computes simple statistics over a list of numbers."""

    def run(self, **inputs: Any) -> Dict[str, Any]:
        raw_values = inputs.get("values", [])
        if not isinstance(raw_values, list):
            raise ValueError("Expected 'values' to be a list")

        values: List[float] = []
        for v in raw_values:
            if v is None:
                continue
            try:
                values.append(float(v))
            except (TypeError, ValueError):
                raise ValueError(f"Non-numeric value in 'values': {v!r}")

        if not values:
            raise ValueError("No numeric values provided in 'values'")

        return {
            "count": len(values),
            "mean": statistics.fmean(values),
            "min": min(values),
            "max": max(values),
            "values": values,
        }
