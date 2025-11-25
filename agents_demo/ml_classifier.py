# agents_demo/ml_classifier.py

from typing import Any, Dict, List

class SimpleMLClassifierAgent:
    """Demo ML classifier: predicts 'class A' or 'class B' from numeric features."""

    def run(self, **inputs: Any) -> Dict[str, Any]:
        features: List[float] = inputs.get("features", [])
        if not isinstance(features, list) or not all(isinstance(x, (int, float)) for x in features):
            raise ValueError("Expected 'features' to be a list of numbers")

        score = sum(features) / (len(features) or 1)
        label = "class A" if score > 0 else "class B"
        return {"score": score, "label": label}
