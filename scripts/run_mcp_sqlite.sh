#!/usr/bin/env bash
set -euo pipefail
source ../.venv/bin/activate
python -m mcp_sqlite_server --db ../db/ventas.db
