#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -ne 1 ]; then
  echo "Usage: $0 <location-id>" >&2
  exit 1
fi

LOCATION_ID="$1"

echo "Deleting location ${LOCATION_ID} from ${BASE_URL} ..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X DELETE "${BASE_URL}/locations/${LOCATION_ID}")

if [ "${HTTP_CODE}" = "204" ]; then
  echo "Location deleted."
else
  echo "Failed to delete location. HTTP ${HTTP_CODE}" >&2
fi
