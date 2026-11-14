#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "ZUHURA: Service Health & Connectivity Check"
echo "=========================================================="

API_URL="${1:-http://localhost:8000/api/v1/health}"

echo "Testing API endpoint: ${API_URL}"
if curl -s -f "${API_URL}" >/dev/null; then
    echo "SUCCESS: Zuhura backend API is healthy."
    curl -s "${API_URL}" | python3 -m json.tool
else
    echo "WARNING: Backend API is not responding at ${API_URL}."
fi
