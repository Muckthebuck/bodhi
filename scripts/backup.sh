#!/usr/bin/env bash
# ============================================================
# Bodhi — Backup Script
# Creates a timestamped compressed backup of all data.
# ============================================================
set -euo pipefail

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
ok()    { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC}  $1"; }
error() { echo -e "${RED}✗${NC} $1" >&2; }

# ── Pre-flight: verify each service is running and healthy ────
_require_healthy() {
  local svc=$1
  local cid
  cid=$(docker compose ps -q "$svc" 2>/dev/null | head -1)
  if [ -z "$cid" ]; then
    error "Service '$svc' is not running — aborting backup"
    rm -rf "$BACKUP_DIR"
    exit 1
  fi
  local health
  health=$(docker inspect --format '{{.State.Health.Status}}' "$cid" 2>/dev/null)
  if [ "$health" = "unhealthy" ]; then
    error "Service '$svc' is unhealthy — aborting backup"
    rm -rf "$BACKUP_DIR"
    exit 1
  fi
}

echo "📦 Creating backup → $BACKUP_DIR"
echo "  Checking service health..."
_require_healthy postgres
_require_healthy neo4j
_require_healthy qdrant
_require_healthy redis
ok "All services healthy"

# PostgreSQL
echo "  Backing up PostgreSQL..."
docker compose exec -T postgres \
  pg_dump -U bodhi bodhi > "$BACKUP_DIR/postgres.sql"
ok "PostgreSQL"

# Neo4j
echo "  Backing up Neo4j..."
docker compose exec -T neo4j \
  neo4j-admin database dump neo4j --to-stdout > "$BACKUP_DIR/neo4j.dump" 2>/dev/null
ok "Neo4j"

# Qdrant (copy storage directory)
echo "  Backing up Qdrant..."
docker cp bodhi-qdrant:/qdrant/storage "$BACKUP_DIR/qdrant-storage"
ok "Qdrant"

# Redis snapshot
echo "  Backing up Redis..."
docker compose exec -T redis redis-cli SAVE > /dev/null
docker cp bodhi-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"
ok "Redis"

# Config
cp .env "$BACKUP_DIR/.env"
cp -r config "$BACKUP_DIR/config"
ok "Config"

# Compress
echo "  Compressing..."
tar -czf "${BACKUP_DIR}.tar.gz" -C "$(dirname "$BACKUP_DIR")" "$(basename "$BACKUP_DIR")"
rm -rf "$BACKUP_DIR"

SIZE=$(du -h "${BACKUP_DIR}.tar.gz" | cut -f1)
ok "Backup complete: ${BACKUP_DIR}.tar.gz (${SIZE})"
