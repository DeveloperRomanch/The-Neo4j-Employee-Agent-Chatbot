#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  PYTHON_EXE="python3"
  if command -v /opt/homebrew/bin/python3 >/dev/null 2>&1; then
    PYTHON_EXE="/opt/homebrew/bin/python3"
  elif command -v python3.14 >/dev/null 2>&1; then
    PYTHON_EXE="python3.14"
  fi
  echo "Creating virtual environment using $PYTHON_EXE..."
  $PYTHON_EXE -m venv .venv
fi

source .venv/bin/activate
pip install -q -r requirements.txt

if command -v docker >/dev/null 2>&1; then
  if ! docker compose ps --status running 2>/dev/null | grep -q neo4j; then
    echo "Starting Neo4j with Docker..."
    docker compose up -d
    echo "Waiting for Neo4j on bolt://localhost:7687..."
    for _ in {1..30}; do
      if (cd app && python - <<'PY'
from graph import EmployeeGraph, load_settings
graph = EmployeeGraph(load_settings())
ok = graph.verify_connectivity()
graph.close()
raise SystemExit(0 if ok else 1)
PY
      ); then
        break
      fi
      sleep 2
    done
  fi
else
  echo "Docker not found. Install Docker Desktop, then run: docker compose up -d"
fi

exec streamlit run app/main.py