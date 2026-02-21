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

# ── OS guard ─────────────────────────────────────────────────
# Bodhi targets Linux hosts (Raspberry Pi 5, x86-64 servers).
# /proc/meminfo and other Linux-specific APIs are used below.
if [ "$(uname -s)" != "Linux" ]; then
  err "This script requires Linux. Detected: $(uname -s)
  For development on macOS/Windows use Docker Desktop and run
  'docker compose up -d' directly."
fi

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
  info "Installing Docker via apt (official Docker repository)..."
  # Install using the package manager rather than piping a remote script
  # directly into sh — avoids supply-chain risk from a mutable URL.
  sudo apt-get update -qq
  sudo apt-get install -y -qq ca-certificates curl gnupg
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/$(. /etc/os-release && echo "$ID")/gpg \
    | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
  sudo chmod a+r /etc/apt/keyrings/docker.gpg
  echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/$(. /etc/os-release && echo "$ID") \
    $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update -qq
  sudo apt-get install -y -qq docker-ce docker-ce-cli containerd.io docker-compose-plugin
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

  ok ".env created with generated secrets — retrieve credentials from .env"
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
# docker inspect is universally available; avoids relying on
# 'docker compose ps --format json' (Compose v2.7+) or python3.
_WAIT=0
while true; do
  _all=true
  for _svc in redis postgres neo4j qdrant; do
    _cid=$(docker compose ps -q "$_svc" 2>/dev/null | head -1)
    if [ -z "$_cid" ]; then
      _all=false; break
    fi
    _status=$(docker inspect --format '{{.State.Health.Status}}' "$_cid" 2>/dev/null)
    if [ "$_status" != "healthy" ]; then
      _all=false; break
    fi
  done
  $_all && break
  if [ "$_WAIT" -ge 120 ]; then
    echo ""
    err "Timed out waiting for databases to become healthy"
    docker compose ps
    exit 1
  fi
  echo -n "."
  sleep 3
  _WAIT=$((_WAIT + 3))
done
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
echo "  Grafana login: admin / <see GRAFANA_PASSWORD in .env>"
echo ""
echo "  Next step: docker compose logs -f"
echo ""
