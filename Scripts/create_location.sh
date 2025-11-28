#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "Usage: $0 <name> [location_type]" >&2
  exit 1
fi

NAME="$1"
TYPE="${2:-local}"

cat >&2 <<EOF
[create_new_location.sh] Creating location:
  name:          ${NAME}
  location_type: ${TYPE}
EOF

curl -s -X POST "${BASE_URL}/locations" \
  -H "Content-Type: application/json" \
  -d @- <<JSON
{
  "name": "${NAME}",
  "location_type": "${TYPE}",
  "config": {},
  "is_active": true
}
JSON
