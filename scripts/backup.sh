#!/usr/bin/env bash
# ============================================================
# Bodhi — Backup Script
# Creates a timestamped compressed backup of all data.
# ============================================================
set -euo pipefail

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

GREEN='\033[0;32m'; NC='\033[0m'
ok() { echo -e "${GREEN}✓${NC} $1"; }

echo "📦 Creating backup → $BACKUP_DIR"

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
