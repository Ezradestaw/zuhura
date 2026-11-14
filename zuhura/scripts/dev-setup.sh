#!/usr/bin/env bash
set -euo pipefail

echo "=========================================================="
echo "Zuhura Mars development setup"
echo "=========================================================="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_ROOT}/.." && pwd)"

echo "Workspace directory: ${WORKSPACE_ROOT}"

# Copy .env if not exists
if [ ! -f "${REPO_ROOT}/.env" ]; then
    echo "Creating .env from .env.example..."
    cp "${REPO_ROOT}/.env.example" "${REPO_ROOT}/.env"
fi

# Verify required host tools
echo "Checking required host tools..."
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required."; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Error: node is required."; exit 1; }

echo "Host tools check passed."
echo "Setup complete. To start the services:"
echo "  cd zuhura/docker && docker compose up -d"
