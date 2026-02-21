#!/usr/bin/env bash
# ============================================================
# Bodhi — Update Script
# Pulls latest code and restarts services with minimal downtime where possible.
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }

echo "🔄 Updating Bodhi..."

# Abort if there are uncommitted local changes — a pull could cause
# merge conflicts or silently overwrite work in progress.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo -e "${YELLOW}⚠${NC}  Uncommitted changes detected. Stash or commit them before updating." >&2
  git status --short >&2
  exit 1
fi

# Capture pre-pull revision so we can diff all changes, not just HEAD~1
PRE_PULL=$(git rev-parse HEAD)

# Pull latest code
git pull origin main
ok "Code updated"

# Pull latest pinned images
docker compose pull --quiet
ok "Images pulled"

# Run DB migrations if any exist (this file is not yet created; guard is intentional)
if [ -f "infra/migrate.sh" ]; then
  echo "  Running migrations..."
  bash infra/migrate.sh
  ok "Migrations complete"
fi

# Diff everything changed since before the pull
CHANGED=$(git diff --name-only "${PRE_PULL}"..HEAD)

# Restart infrastructure only if the production compose file changed.
# Deliberately excludes docker-compose.dev.yml — dev overrides should
# not trigger production restarts.
if echo "$CHANGED" | grep -qE '^docker-compose\.yml$'; then
  warn "docker-compose.yml changed — restarting infrastructure"
  docker compose up -d redis postgres neo4j qdrant
fi

# Restart monitoring only if config changed
if echo "$CHANGED" | grep -q "monitoring/"; then
  warn "Monitoring config changed — restarting stack"
  docker compose up -d node-exporter postgres-exporter redis-exporter prometheus grafana loki promtail
fi

# Restart application services (rolling, when they exist).
# After each restart, wait for the container to become healthy
# (or running if no healthcheck is defined) before moving on.
_wait_for_service() {
  local svc=$1 waited=0 limit=60
  local cid
  cid=$(docker compose ps -q "$svc" 2>/dev/null | head -1)
  [ -z "$cid" ] && return 0
  while [ "$waited" -lt "$limit" ]; do
    local health state
    health=$(docker inspect --format '{{.State.Health.Status}}' "$cid" 2>/dev/null)
    state=$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null)
    # No healthcheck defined — just check it's running
    if [ -z "$health" ] && [ "$state" = "running" ]; then return 0; fi
    # Has a healthcheck — wait for healthy
    if [ "$health" = "healthy" ]; then return 0; fi
    if [ "$health" = "unhealthy" ]; then
      warn "${svc} became unhealthy after restart"
      return 1
    fi
    sleep 3; waited=$((waited + 3))
  done
  warn "${svc} did not become healthy within ${limit}s — continuing"
}

for service in central-agent language-center memory-manager emotion-regulator \
               skill-executor tool-coordinator visual-agent auditory-agent \
               voice-synthesizer motor-controller api-gateway; do
  if docker compose ps --services | grep -q "^${service}$"; then
    echo "  Restarting ${service}..."
    docker compose up -d --no-deps "$service"
    _wait_for_service "$service"
  fi
done

ok "Update complete"
docker compose ps
