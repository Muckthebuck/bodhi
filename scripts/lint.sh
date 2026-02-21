#!/usr/bin/env bash
# Usage: ./scripts/lint.sh [--fix]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "${1:-}" == "--fix" ]]; then
  echo "→ ruff (fix)"
  ruff check services/ tests/ --fix
  ruff format services/ tests/
else
  echo "→ ruff (check)"
  ruff check services/ tests/
  ruff format services/ tests/ --check
fi

echo "→ mypy"
for svc in central-agent language-center memory-manager emotion-regulator; do
  echo "   checking services/$svc/main.py"
  (cd "services/$svc" && mypy main.py --ignore-missing-imports --no-error-summary) || exit 1
done

echo "All lint checks passed ✅"
