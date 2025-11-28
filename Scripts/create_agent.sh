#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

NAME=${1:-simple-demo-agent}
VERSION=${2:-0.1.0}
OWNER=${3:-"ian"}

# Human-readable note → stderr
cat >&2 <<EOF
[create_agent.sh] Creating agent:
  name:        ${NAME}
  version:     ${VERSION}
  owner:       ${OWNER}
  entrypoint:  agents_demo.simple_agent:SimpleDemoAgent
  git_repo:    https://github.com/ianfoster/agent-repository
EOF

# JSON → stdout only
curl -s -X POST "${BASE_URL}/agents" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "name": "${NAME}",
  "version": "${VERSION}",
  "description": "A simple demo agent created from create_agent.sh",
  "agent_type": "task",
  "tags": ["example", "demo", "cli"],
  "owner": "${OWNER}",
  "inputs_schema": {},
  "outputs_schema": {},
  "git_repo": "https://github.com/ianfoster/agent-repository",
  "git_commit": "",
  "container_image": "",
  "entrypoint": "agents_demo.simple_agent:SimpleDemoAgent"
}
JSON
