# Academy Agent Repository

This repository implements an **Agent Registry + Catalog** for the Academy middleware, together with:

- a **FastAPI backend** for storing and serving agent specifications,
- a **React frontend** for browsing, filtering, and inspecting agents,
- a **Python SDK + CLI** (`academy-agents`) for registering and running agents,
- and **examples** of agent implementations that can be executed locally.

The goal is to make it easy for model and lab teams to **publish, discover, validate, and run** agents that wrap scientific capabilities (HPC workflows, lab protocols, data processing, etc.).

---

## Repository Layout

At a high level:

```text
backend/        FastAPI backend (Agent registry API + DB models)
frontend/       React + Vite frontend (Agent catalog UI)
sdk/            Python SDK + CLI (academy-agents)
agents_demo/    Example Python agent implementations
examples/
  simple-demo-agent/
    agent.yaml          Agent spec for the SimpleDemoAgent
    inputs/hello.json   Example inputs
```

### Backend

- `backend/app/main.py` – FastAPI app with endpoints such as:
  - `GET /health`
  - `GET /agents`, `POST /agents`
  - `GET /agents/{id}`
  - `POST /agents/{id}/validate`
  - `POST /agents/{id}/deploy`
  - `GET /agents/{id}/deployments`
- `backend/app/models.py` – SQLAlchemy models for:
  - `Agent` (metadata, schema, A2A card, GitHub/container, validation)
  - `Deployment` (stub deployment records)
- `backend/app/schemas.py` – Pydantic models used as API schemas.
- `backend/app/crud.py` – Agent and deployment CRUD operations.

The backend currently uses SQLite for local development, but can be pointed at Postgres via `DATABASE_URL`.

### Frontend

- `frontend/src/App.tsx` – main catalog UI:
  - filters (name, type, tag, owner)
  - list of agents with validation status and GitHub links
  - detail view with:
    - agent metadata and ID (with "Copy ID")
    - validation status and score (with "Mark as validated")
    - deployment history and "Create deployment" button
    - A2A card summary
    - raw JSON

### SDK / CLI

- `sdk/academy_agents/client.py` – `AgentClient` for talking to the backend.
- `sdk/academy_agents/cli.py` – `academy-agents` CLI entry point.
- `sdk/academy_agents/runner.py` – `run-local` helper to execute agents from GitHub.

Key CLI commands:

```bash
academy-agents init agent.yaml                  # create a template spec
academy-agents register agent.yaml --base-url … # register an agent
academy-agents list --base-url …                # list agents
academy-agents show <id-or-name> --base-url …   # show full spec
academy-agents validate <id> --score 0.93       # mark validated
academy-agents deploy <id> --target dev         # stub deployment record
academy-agents run-local <id-or-name>           # run agent code on laptop
```

---

## Agent Model

In this repository, an **agent** is treated as a **specification**, not a running service.

An agent is represented by an `AgentSpec` that includes:

- **Core metadata**
  - `name`, `version`, `description`
  - `agent_type` (task, domain, planner, tool-wrapper, etc.)
  - `tags`, `owner`
- **Interface schema**
  - `inputs` (named fields with type/description/required)
  - `outputs`
- **A2A Agent Card**
  - `a2a_card` block with `name`, `url`, `version`, `capabilities`, etc.
- **Implementation metadata**
  - `git_repo` – GitHub URL of the repo containing the code
  - `git_commit` – optional commit SHA to pin exact version
  - `container_image` – optional container image reference
  - `entrypoint` – Python module and attribute, e.g. `agents_demo.simple_agent:SimpleDemoAgent`
- **Validation metadata**
  - `validation_status` (`unvalidated`, `validated`, etc.)
  - `validation_score`
  - `last_validated_at`
- **Deployment metadata (indirectly)**
  - separate `Deployment` records, linked by `agent_id`

At runtime:

- the **backend** stores `AgentSpec` objects in the DB,
- the **SDK** fetches specs and exposes Python methods,
- the **CLI** lets users register, show, validate, deploy, and run agents.

---

## Running the System Locally

### Prerequisites

- Python 3.10+ (3.11 recommended)
- Node.js (18+ recommended)
- `git` on your PATH

### 1. Backend (FastAPI)

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

This starts the API at:

```
http://localhost:8000
```

Health check:

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"backend"}
```

### 2. Frontend (React + Vite)

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

Open in a browser:

```
http://localhost:5173
```

You should see:

- a green "Backend is healthy" tick,
- an empty or populated agents table (depending on what is registered).

### 3. SDK / CLI

In another terminal:

```bash
cd sdk
pip install -e ".[dev]"
```

List agents (may be empty at first):

```bash
academy-agents list --base-url http://localhost:8000
```

---

## Example: Simple Demo Agent

A fully working example agent is included:

```text
agents_demo/
  __init__.py
  simple_agent.py

examples/
  simple-demo-agent/
    README.md
    agent.yaml
    inputs/
      hello.json
```

`agents_demo/simple_agent.py` defines:

```python
class SimpleDemoAgent:
    def run(self, **inputs) -> dict:
        name = inputs.get("name", "world")
        return {
            "greeting": f"Hello, {name}! This agent ran on your laptop.",
            "received_inputs": inputs,
        }
```

`examples/simple-demo-agent/agent.yaml` describes it to the registry, including:

```yaml
name: simple-demo-agent
git_repo: "https://github.com/ianfoster/agent-repository"
entrypoint: "agents_demo.simple_agent:SimpleDemoAgent"
inputs:
  name:
    type: "string"
    required: true
```

and example inputs in `inputs/hello.json`:

```json
{
  "name": "Ian"
}
```

### Register the demo agent

From `sdk/`:

```bash
academy-agents register ../examples/simple-demo-agent/agent.yaml \
  --base-url http://localhost:8000
```

You can verify:

```bash
academy-agents list --base-url http://localhost:8000
academy-agents show simple-demo-agent --base-url http://localhost:8000
```

The agent will also appear in the web UI.

### Run the demo agent locally

From `sdk/`:

```bash
academy-agents run-local simple-demo-agent \
  --base-url http://localhost:8000 \
  --inputs ../examples/simple-demo-agent/inputs/hello.json \
  --workdir ~/.academy/agents
```

This will:

1. fetch the `simple-demo-agent` spec from the backend,
2. clone/update `git_repo` into `~/.academy/agents/simple-demo-agent`,
3. import `agents_demo.simple_agent:SimpleDemoAgent`,
4. call `run(name="Ian")`,
5. print the result,
6. record a stub `Deployment` with `target="local"`.

---

## Development & Testing

### Backend tests

```bash
cd backend
pytest
```

Tests use a temporary SQLite DB (`test_agents.db`) and override the `get_db` dependency.

### SDK tests

```bash
cd sdk
pytest
```

Most tests use monkeypatched `httpx` so they do not require a running backend. One "live" health test is marked as skipped by default.

### Frontend build

```bash
cd frontend
npm run build
```

For development:

```bash
npm run dev
```

---

## Future Directions

Planned / possible extensions:

- **Per-agent virtual environments** for isolated dependencies.
- **Remote execution** (HPC, lab nodes, cloud) integrated with the `/deploy` story.
- **Richer A2A support**, including exportable A2A cards and more complete skill descriptions.
- **Governance metadata** (maturity, canonical agents, ownership model).
- **Agent templates and scaffolding** for external teams.

---

## Getting Help

This repository is still evolving. If something is confusing or breaks:

- Check the example in `examples/simple-demo-agent/`.
- Use the `academy-agents show` command to inspect what was actually registered.
- Inspect backend logs from `uvicorn app.main:app --reload`.
- Try clearing cached clones for a given agent:

```bash
rm -rf ~/.academy/agents/<agent-name>
```

Happy hacking 🚀
