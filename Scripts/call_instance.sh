#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -ne 3 ]; then
  echo "Usage: $0 <instance-id> <action> <json-payload>" >&2
  echo "Example payload: '{\"name\": \"Ian\"}'" >&2
  exit 1
fi

INSTANCE_ID="$1"
ACTION="$2"
PAYLOAD="$3"

cat >&2 <<EOF
[call_instance.sh] Calling:
  instance_id: ${INSTANCE_ID}
  action:      ${ACTION}
  payload:     ${PAYLOAD}
EOF

RESPONSE_FILE=$(mktemp)
HTTP_CODE=$(curl -s -o "${RESPONSE_FILE}" -w "%{http_code}" \
  -X POST "${BASE_URL}/instances/${INSTANCE_ID}/call" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "action": "${ACTION}",
  "payload": ${PAYLOAD}
}
JSON
)

RESPONSE_BODY=$(cat "${RESPONSE_FILE}")
rm -f "${RESPONSE_FILE}"

if [ "${HTTP_CODE}" = "200" ]; then
  echo "${RESPONSE_BODY}"
else
  cat >&2 <<EOF
[call_instance.sh] ERROR: HTTP ${HTTP_CODE} from ${BASE_URL}/instances/${INSTANCE_ID}/call
[call_instance.sh] Response body:
${RESPONSE_BODY}
EOF
  exit 1
fi
