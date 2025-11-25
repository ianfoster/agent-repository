# agents_demo/materials_screening.py

import random
from typing import Any, Dict, List

class MaterialsScreeningAgent:
    """Demo agent that assigns stability scores to materials."""

    def run(self, **inputs: Any) -> Dict[str, Any]:
        materials: List[str] = inputs.get("materials", [])
        if not isinstance(materials, list) or not all(isinstance(m, str) for m in materials):
            raise ValueError("Expected 'materials' to be a list of strings")

        results = []
        for m in materials:
            score = random.uniform(0, 1)
            label = (
                "promising" if score > 0.75 else
                "borderline" if score > 0.3 else
                "poor"
            )
            results.append({"material": m, "score": score, "label": label})

        return {"results": results}
