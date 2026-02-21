#!/usr/bin/env bash
# ============================================================
# Bodhi — Setup Script
# Run once on a fresh install.
# ============================================================
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC}  $1"; }
err()  { echo -e "${RED}✗${NC} $1"; exit 1; }
info() { echo -e "  $1"; }

echo ""
echo "╔══════════════════════════════════════╗"
echo "║        Bodhi — Setup                 ║"
echo "╚══════════════════════════════════════╝"
echo ""

# ── Architecture detect ──────────────────────────────────────
ARCH=$(uname -m)
case "$ARCH" in
  aarch64) ARCH=arm64 ;;
  x86_64)  ARCH=amd64 ;;
  *) err "Unsupported architecture: $ARCH" ;;
esac
ok "Architecture: $ARCH"

# ── System requirements ──────────────────────────────────────
FREE_RAM_MB=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
FREE_DISK_GB=$(df -BG . | awk 'NR==2 {gsub("G","",$4); print $4}')

if [ "$FREE_RAM_MB" -lt 5000 ]; then
  warn "Less than 5 GB RAM free (${FREE_RAM_MB} MB). Performance may degrade."
  read -rp "  Continue anyway? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || exit 1
else
  ok "RAM: ${FREE_RAM_MB} MB free"
fi

if [ "$FREE_DISK_GB" -lt 20 ]; then
  err "Less than 20 GB disk space free (${FREE_DISK_GB} GB). Aborting."
fi
ok "Disk: ${FREE_DISK_GB} GB free"

# ── Docker ───────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  info "Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER"
  warn "Added $USER to docker group. Log out and back in, then re-run this script."
  exit 0
fi
ok "Docker: $(docker --version | cut -d' ' -f3 | tr -d ',')"

if ! docker compose version &>/dev/null; then
  err "Docker Compose plugin not found. Install Docker Desktop or 'docker compose' plugin."
fi
ok "Docker Compose: $(docker compose version --short)"

# ── .env file ────────────────────────────────────────────────
if [ ! -f .env ]; then
  info "Generating .env from template..."
  cp .env.example .env

  PG_PASS=$(openssl rand -hex 16)
  NEO_PASS=$(openssl rand -hex 16)
  GF_PASS=$(openssl rand -hex 12)

  sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${PG_PASS}/" .env
  sed -i "s/^NEO4J_PASSWORD=.*/NEO4J_PASSWORD=${NEO_PASS}/" .env
  sed -i "s/^GRAFANA_PASSWORD=.*/GRAFANA_PASSWORD=${GF_PASS}/" .env
  sed -i "s/^ARCH=.*/ARCH=${ARCH}/" .env

  ok ".env created with generated secrets"
  info "Grafana password: ${GF_PASS}  (also stored in .env)"
else
  ok ".env already exists — skipping"
fi

# ── Directory structure ──────────────────────────────────────
mkdir -p models/{piper,whisper} config certs logs
ok "Directories ready"

# ── Pull images ──────────────────────────────────────────────
info "Pulling Docker images (this may take a few minutes)..."
docker compose pull --quiet
ok "Images pulled"

# ── Start infrastructure ─────────────────────────────────────
info "Starting infrastructure services..."
docker compose up -d redis postgres neo4j qdrant

info "Waiting for databases to be healthy..."
timeout 120 bash -c '
  until docker compose ps --format json | python3 -c "
import sys, json
services = [json.loads(l) for l in sys.stdin if l.strip()]
infra = [s for s in services if s[\"Service\"] in [\"redis\",\"postgres\",\"neo4j\",\"qdrant\"]]
all_healthy = all(s.get(\"Health\",\"\") in [\"healthy\",\"\"] for s in infra)
sys.exit(0 if all_healthy else 1)
" 2>/dev/null; do
    echo -n "."
    sleep 3
  done
'
ok "Databases healthy"

# ── Start monitoring ─────────────────────────────────────────
info "Starting monitoring stack..."
docker compose up -d prometheus grafana loki promtail
ok "Monitoring started"

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Bodhi infrastructure is running! 🎉    ║"
echo "╚══════════════════════════════════════════╝"
echo ""
echo "  Grafana:    http://localhost:3000"
echo "  Prometheus: http://localhost:9090"
echo ""
GRAFANA_PASS=$(grep GRAFANA_PASSWORD .env | cut -d= -f2)
echo "  Grafana login: admin / ${GRAFANA_PASS}"
echo ""
echo "  Next step: docker compose logs -f"
echo ""
