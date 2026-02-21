#!/usr/bin/env bash
# ============================================================
# Bodhi — Update Script
# Pulls latest code and restarts services with zero downtime.
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }

echo "🔄 Updating Bodhi..."

# Capture pre-pull revision so we can diff all changes, not just HEAD~1
PRE_PULL=$(git rev-parse HEAD)

# Pull latest code
git pull origin main
ok "Code updated"

# Pull latest pinned images
docker compose pull --quiet
ok "Images pulled"

# Run DB migrations if any exist
if [ -f "infra/migrate.sh" ]; then
  echo "  Running migrations..."
  bash infra/migrate.sh
  ok "Migrations complete"
fi

# Diff everything changed since before the pull
CHANGED=$(git diff --name-only "${PRE_PULL}"..HEAD)

# Restart infrastructure only if compose config changed
if echo "$CHANGED" | grep -q "docker-compose"; then
  warn "docker-compose.yml changed — restarting infrastructure"
  docker compose up -d redis postgres neo4j qdrant
fi

# Restart monitoring only if config changed
if echo "$CHANGED" | grep -q "monitoring/"; then
  warn "Monitoring config changed — restarting stack"
  docker compose up -d node-exporter prometheus grafana loki promtail
fi

# Restart application services (rolling, when they exist)
for service in central-agent language-center memory-manager emotion-regulator \
               skill-executor tool-coordinator visual-agent auditory-agent \
               voice-synthesizer motor-controller api-gateway; do
  if docker compose ps --services | grep -q "^${service}$"; then
    echo "  Restarting ${service}..."
    docker compose up -d --no-deps "$service"
    sleep 3
  fi
done

ok "Update complete"
docker compose ps
