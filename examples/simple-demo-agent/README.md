# Simple Demo Agent

This directory contains a fully working **example agent** that demonstrates how to:

- implement an agent in Python,
- describe it using an `agent.yaml` specification,
- register it with the Academy Agent Repository backend,
- run it locally on your laptop using the `academy-agents` CLI,
- and view its validation & deployment history in the UI.

This example is the recommended starting point for developing new agents.

---

## Directory Structure

```
examples/simple-demo-agent/
    README.md               ← this file
    agent.yaml              ← agent specification for the registry
    inputs/
      hello.json            ← example input payload for local execution
```

The Python implementation for this demo agent lives at the repo root:

```
agents_demo/
    __init__.py
    simple_agent.py
```

---

## Python Implementation

The agent is implemented in `agents_demo/simple_agent.py`:

```python
from __future__ import annotations
from typing import Any, Dict

class SimpleDemoAgent:
    # Minimal agent implementation for demo purposes.
    # Must implement run(**inputs) -> dict.
    def run(self, **inputs: Any) -> Dict[str, Any]:
        name = inputs.get("name", "world")
        return {
            "greeting": f"Hello, {name}! This agent ran on your laptop.",
            "received_inputs": inputs,
        }
```

This is the object executed by the CLI via:

```yaml
entrypoint: "agents_demo.simple_agent:SimpleDemoAgent"
```

---

## Agent Specification (`agent.yaml`)

The `agent.yaml` file describes the agent to the registry. Important fields:

```yaml
name: simple-demo-agent
git_repo: "https://github.com/ianfoster/agent-repository"
entrypoint: "agents_demo.simple_agent:SimpleDemoAgent"
inputs:
  name:
    type: "string"
    required: true
```

Example input:

```
inputs/hello.json
```

```json
{
  "name": "Ian"
}
```

---

## 1. Register the Agent with the Registry

Start the backend:

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Then register the agent:

```bash
cd sdk
pip install -e ".[dev]"

academy-agents register ../examples/simple-demo-agent/agent.yaml \
  --base-url http://localhost:8000
```

Check it:

```bash
academy-agents list --base-url http://localhost:8000
academy-agents show simple-demo-agent --base-url http://localhost:8000
```

Visit in browser:

```
http://localhost:5173
```

---

## 2. Run the Agent Locally

From the `sdk` directory:

```bash
academy-agents run-local simple-demo-agent \
  --base-url http://localhost:8000 \
  --inputs ../examples/simple-demo-agent/inputs/hello.json \
  --workdir ~/.academy/agents
```

This will:

1. fetch the agent spec  
2. clone/update the GitHub repo  
3. import the Python entrypoint  
4. load inputs  
5. execute `run(**inputs)`  
6. print the result  
7. record a `"local"` deployment  

Typical output:

```json
{
  "greeting": "Hello, Ian! This agent ran on your laptop.",
  "received_inputs": { "name": "Ian" }
}
```

---

## 3. View in the UI

Open:

```
http://localhost:5173
```

Select **simple-demo-agent** to see:

- validation status and score  
- “Mark as validated” button  
- deployment history  
- GitHub metadata  
- A2A Card details  
- raw JSON  

---

## 4. Create Your Own Agents

To build a new agent from this template:

```bash
cp -r examples/simple-demo-agent examples/my-new-agent
```

Edit:

- `examples/my-new-agent/agent.yaml`
- `agents_demo/my_new_agent.py`

Register and run:

```bash
academy-agents register ../examples/my-new-agent/agent.yaml --base-url http://localhost:8000
academy-agents run-local my-new-agent --inputs ...
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'agents_demo'

Make sure:

- `agents_demo/` is at repo root  
- `__init__.py` exists  
- you committed/pushed changes  
- clear cached clones:

```bash
rm -rf ~/.academy/agents/simple-demo-agent
```

---

Happy hacking! 🎉
