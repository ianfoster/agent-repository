#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -ne 1 ]; then
  echo "Usage: $0 <agent-id>" >&2
  exit 1
fi

AGENT_ID="$1"

echo "Deleting agent ${AGENT_ID} from ${BASE_URL} ..."
curl -s -o /dev/null -w "%{http_code}\n" \
  -X DELETE "${BASE_URL}/agents/${AGENT_ID}"
