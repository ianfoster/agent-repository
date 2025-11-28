#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -ne 2 ]; then
  echo "Usage: $0 <agent-id> <location-name>" >&2
  exit 1
fi

AGENT_ID="$1"
LOCATION_NAME="$2"

cat >&2 <<EOF
[start_instance.sh] Starting instance:
  agent_id:      ${AGENT_ID}
  location_name: ${LOCATION_NAME}
EOF

# Capture response and HTTP status separately
RESPONSE_FILE=$(mktemp)
HTTP_CODE=$(curl -s -o "${RESPONSE_FILE}" -w "%{http_code}" \
  -X POST "${BASE_URL}/agents/${AGENT_ID}/instances" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "location_name": "${LOCATION_NAME}",
  "init_inputs": {}
}
JSON
)

RESPONSE_BODY=$(cat "${RESPONSE_FILE}")
rm -f "${RESPONSE_FILE}"

if [ "${HTTP_CODE}" = "200" ]; then
  # Successful start → output JSON only (stdout)
  echo "${RESPONSE_BODY}"
else
  # Error → log to stderr and exit non-zero
  cat >&2 <<EOF
[start_instance.sh] ERROR: HTTP ${HTTP_CODE} from ${BASE_URL}/agents/${AGENT_ID}/instances
[start_instance.sh] Response body:
${RESPONSE_BODY}
EOF
  exit 1
fi
