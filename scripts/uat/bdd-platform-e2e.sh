#!/usr/bin/env bash
set -euo pipefail

# E2E smoke script for BDD Platform APIs.
# Requires: BASE_URL, PROJECT_ID, FEATURE_ID, TEST_PLAN_ID, SCENARIO_ID

BASE_URL="${BASE_URL:-http://localhost:8000}"
PROJECT_ID="${PROJECT_ID:-}"
FEATURE_ID="${FEATURE_ID:-}"
TEST_PLAN_ID="${TEST_PLAN_ID:-}"
SCENARIO_ID="${SCENARIO_ID:-}"

if [[ -z "$PROJECT_ID" || -z "$FEATURE_ID" || -z "$TEST_PLAN_ID" || -z "$SCENARIO_ID" ]]; then
  echo "Missing env vars. Set PROJECT_ID, FEATURE_ID, TEST_PLAN_ID, SCENARIO_ID." >&2
  exit 1
fi

echo "== Git sync =="
curl -sS -X POST "$BASE_URL/api/v1/projects/$PROJECT_ID/sync" | jq

echo "== Edit feature =="
cat <<'EOF' > /tmp/bdd_feature_edit.feature
Feature: Auth
  Scenario: Login success
    Given user exists
    When user logs in
    Then user sees dashboard
EOF
curl -sS -X PUT "$BASE_URL/api/v1/projects/$PROJECT_ID/features/$FEATURE_ID" \
  -H "Content-Type: application/json" \
  -d @- <<JSON | jq
{"content": "$(sed 's/"/\\"/g' /tmp/bdd_feature_edit.feature | tr '\n' '\\n')", "commit_message": "chore: update auth.feature"}
JSON

echo "== Trigger execution =="
RUN_RESPONSE=$(curl -sS -X POST "$BASE_URL/api/v1/projects/$PROJECT_ID/test-runs" \
  -H "Content-Type: application/json" \
  -d '{"scope_type":"project"}')
TEST_RUN_ID=$(echo "$RUN_RESPONSE" | jq -r .id)
echo "TestRun: $TEST_RUN_ID"

echo "== Stream logs (first 20 lines) =="
curl -sS "$BASE_URL/api/v1/projects/$PROJECT_ID/test-runs/$TEST_RUN_ID/logs" | head -n 20

echo "== Create hybrid execution =="
EXEC_RESPONSE=$(curl -sS -X POST "$BASE_URL/api/v1/projects/$PROJECT_ID/scenario-executions" \
  -H "Content-Type: application/json" \
  -d "{\"scenario_id\":\"$SCENARIO_ID\",\"test_plan_item_id\":\"$TEST_PLAN_ID\"}")
EXEC_ID=$(echo "$EXEC_RESPONSE" | jq -r .id)
RECORD_ID=$(echo "$EXEC_RESPONSE" | jq -r '.steps[0].id')

echo "== Manual step update =="
curl -sS -X PATCH "$BASE_URL/api/v1/projects/$PROJECT_ID/scenario-executions/$EXEC_ID/steps/$RECORD_ID/manual" \
  -H "Content-Type: application/json" \
  -d '{"status":"pass","notes":"manual pass"}' | jq

echo "E2E script completed."
