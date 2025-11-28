#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -ne 2 ]; then
  echo "Usage: $0 <agent-id> <location-id>" >&2
  exit 1
fi

AGENT_ID="$1"
LOCATION_ID="$2"

cat >&2 <<EOF
[deploy_agent.sh] Deploying:
  agent_id:    ${AGENT_ID}
  location_id: ${LOCATION_ID}
EOF

# Capture response body and HTTP code separately
RESPONSE_FILE=$(mktemp)
HTTP_CODE=$(curl -s -o "${RESPONSE_FILE}" -w "%{http_code}" \
  -X POST "${BASE_URL}/deployments" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "agent_id": "${AGENT_ID}",
  "location_id": "${LOCATION_ID}"
}
JSON
)

RESPONSE_BODY=$(cat "${RESPONSE_FILE}")
rm -f "${RESPONSE_FILE}"

# Print JSON response only on success (to stdout)
if [ "${HTTP_CODE}" = "201" ]; then
  # assume JSON on success
  echo "${RESPONSE_BODY}"
else
  # Log error details to stderr
  cat >&2 <<EOF
[deploy_agent.sh] ERROR: HTTP ${HTTP_CODE} from ${BASE_URL}/deployments
[deploy_agent.sh] Response body:
${RESPONSE_BODY}
EOF
  exit 1
fi
