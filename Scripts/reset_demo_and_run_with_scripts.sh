#!/usr/bin/env bash
set -euo pipefail

# Directory where this script (and helper scripts) live
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BASE_URL=${BASE_URL:-http://localhost:8000}

echo "=== Reset + demo using helper scripts (base_url=${BASE_URL}) ==="

#------------------------------------------------------------
# 1. Delete all agents
#------------------------------------------------------------
echo
echo "Deleting all agents..."
AGENTS_JSON="$("${SCRIPT_DIR}/list_all_agents.sh" 2>/dev/null || echo '[]')"

echo "${AGENTS_JSON}" | jq -r '.[].id' | while read -r AID; do
  if [ -n "${AID}" ]; then
    echo "  ./delete_agent.sh ${AID}"
    "${SCRIPT_DIR}/delete_agent.sh" "${AID}" || true
  fi
done

#------------------------------------------------------------
# 2. Delete all locations
#------------------------------------------------------------
echo
echo "Deleting all locations..."
LOCS_JSON="$("${SCRIPT_DIR}/list_locations.sh" 2>/dev/null || echo '[]')"

echo "${LOCS_JSON}" | jq -r '.[].id' | while read -r LID; do
  if [ -n "${LID}" ]; then
    echo "  ./delete_location.sh ${LID}"
    "${SCRIPT_DIR}/delete_location.sh" "${LID}" || true
  fi
done

#------------------------------------------------------------
# 3. Create demo agent
#------------------------------------------------------------
echo
echo "Creating demo agent simple-demo-agent via create_agent.sh..."

# NOTE: redirect stderr so we capture only JSON from stdout
AGENT_JSON="$("${SCRIPT_DIR}/create_agent.sh" simple-demo-agent 0.1.0 demo-user 2>/dev/null)"

echo "${AGENT_JSON}" | jq
AGENT_ID=$(echo "${AGENT_JSON}" | jq -r '.id')
echo "Created agent simple-demo-agent with id: ${AGENT_ID}"

#------------------------------------------------------------
# 4. Create location DEMO-LOC
#------------------------------------------------------------
echo
echo "Creating location DEMO-LOC via create_location.sh..."

LOC_JSON="$("${SCRIPT_DIR}/create_location.sh" DEMO-LOC local 2>/dev/null)"

echo "${LOC_JSON}" | jq
LOCATION_ID=$(echo "${LOC_JSON}" | jq -r '.id')
echo "Created location DEMO-LOC with id: ${LOCATION_ID}"

#------------------------------------------------------------
# 5. Deploy demo agent at DEMO-LOC
#------------------------------------------------------------
echo
echo "Deploying demo agent at DEMO-LOC via deploy_agent.sh..."

# We don't parse this JSON now, but we do care about success/failure.
# If deploy_agent.sh exits non-zero, this script will exit because of set -e.
DEPLOY_JSON="$("${SCRIPT_DIR}/deploy_agent.sh" "${AGENT_ID}" "${LOCATION_ID}" 2>/dev/null)"

# Optionally show the deployment JSON if you want:
if [ -n "${DEPLOY_JSON}" ]; then
  echo "${DEPLOY_JSON}" | jq
fi

echo "Deployment completed successfully."

#------------------------------------------------------------
# 6. Start instance of demo agent at DEMO-LOC
#------------------------------------------------------------
echo
echo "Starting instance via start_instance.sh..."

INSTANCE_JSON="$("${SCRIPT_DIR}/start_instance.sh" "${AGENT_ID}" DEMO-LOC 2>/dev/null)"

echo "${INSTANCE_JSON}" | jq
INSTANCE_ID=$(echo "${INSTANCE_JSON}" | jq -r '.instance_id')
echo "Started instance with id: ${INSTANCE_ID}"

#------------------------------------------------------------
# 7. Call the deployed agent (greet) via call_instance.sh
#------------------------------------------------------------
echo
echo "Calling greet on instance ${INSTANCE_ID} via call_instance.sh..."

CALL_JSON="$("${SCRIPT_DIR}/call_instance.sh" "${INSTANCE_ID}" greet '{"name": "Demo User"}' 2>/dev/null)"

echo "Call result:"
echo "${CALL_JSON}" | jq

echo
echo "=== Demo reset + deploy + run via helper scripts completed ==="
