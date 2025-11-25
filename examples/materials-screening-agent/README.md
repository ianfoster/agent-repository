# Materials Screening Agent

This directory defines a **demo agent** that assigns a simple "stability" score
to each input material and classifies them as:

- **promising** (score > 0.75)
- **borderline** (0.3 < score ≤ 0.75)
- **poor** (score ≤ 0.3)

The implementation uses a random score in [0, 1] for illustration; the goal is
to demonstrate the end-to-end flow (publish → deploy from GitHub → run) rather
than provide a real model.

## Files

- `materials_screening.py`  
  Python implementation of `MaterialsScreeningAgent`.

- `agent.yaml`  
  Agent specification used by the registry.

- `inputs/example.json`  
  Example inputs for local runs.

## Python Implementation

```python
class MaterialsScreeningAgent:
    def run(self, **inputs):
        # expects inputs["materials"] to be a list of strings
        ...
```

## Example Inputs

```json
{
  "materials": ["Fe2O3", "TiO2", "PbS", "Cu2O"]
}
```

## Usage (CLI)

Assuming this repo is cloned and the backend is running:

```bash
cd sdk
pip install -e ".[dev]"

# Register the agent
academy-agents register ../examples/materials-screening-agent/agent.yaml \
  --base-url http://localhost:8000

# Run locally via CLI
academy-agents run-local materials-screening-agent \
  --base-url http://localhost:8000 \
  --inputs ../examples/materials-screening-agent/inputs/example.json \
  --workdir ~/.academy/agents
```

## Usage (UI)

1. Open the frontend at http://localhost:5173  
2. Select **materials-screening-agent** in the catalog  
3. Set target (e.g. `local-ui`) and click **Deploy (stage code)**  
4. Paste the example JSON into the Run inputs box and click **Run agent**  
5. View results in the **Last run outputs** panel.
