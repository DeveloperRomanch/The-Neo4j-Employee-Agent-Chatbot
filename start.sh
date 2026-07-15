#!/usr/bin/env bash
set -euo pipefail

# Find script directory to run from anywhere
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Running app launch script..."
./run.sh
