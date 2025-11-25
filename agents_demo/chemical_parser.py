# agents_demo/chemical_parser.py

from typing import Any, Dict
import re

class ChemicalFormulaParserAgent:
    """Parses a chemical formula and counts atoms."""

    pattern = re.compile(r"([A-Z][a-z]?)(\d*)")

    def run(self, **inputs: Any) -> Dict[str, Any]:
        formula = inputs.get("formula")
        if not isinstance(formula, str):
            raise ValueError("Expected 'formula' to be a string")

        counts: Dict[str, int] = {}
        for elem, num in self.pattern.findall(formula):
            n = int(num) if num else 1
            counts[elem] = counts.get(elem, 0) + n

        return {"formula": formula, "counts": counts}
