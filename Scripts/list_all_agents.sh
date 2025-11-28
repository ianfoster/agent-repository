#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}

curl -s "${BASE_URL}/agents" | jq
