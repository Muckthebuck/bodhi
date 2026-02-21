"""
Infrastructure validation tests.

Config/compose file checks use YAML parsing (no docker CLI needed).
Service health checks use protocol-native connections (runs inside the network).
"""

import os
import re
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent.parent


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


@pytest.mark.smoke
class TestComposeConfig:
    def test_compose_config_valid(self):
        """Both compose files must be valid YAML with a 'services' key."""
        for fname in ("docker-compose.yml", "docker-compose.dev.yml"):
            data = yaml.safe_load((ROOT / fname).read_text())
            assert "services" in data, f"{fname} is missing the 'services' key"

    def test_no_latest_image_tags(self):
        """External (third-party) images must be pinned to explicit versions — no :latest.
        Internal bodhi/* images are exempt as they are always built locally."""
        compose = (ROOT / "docker-compose.yml").read_text()
        latest_lines = [
            line.strip()
            for line in compose.splitlines()
            if re.search(r"image:.*:latest", line) and not re.search(r"image:\s*bodhi/", line)
        ]
        assert not latest_lines, "Found :latest tags on external images:\n" + "\n".join(
            latest_lines
        )

    def test_no_deploy_resources_blocks(self):
        """deploy.resources.limits is Swarm-only and silently ignored — must not exist."""
        compose = (ROOT / "docker-compose.yml").read_text()
        assert "deploy:" not in compose, (
            "Found 'deploy:' in docker-compose.yml — use mem_limit/cpus instead"
        )

    def test_env_example_has_all_required_keys(self):
        """Every key in .env.example must be documented."""
        required = {"POSTGRES_PASSWORD", "NEO4J_PASSWORD", "GRAFANA_PASSWORD"}
        env_text = (ROOT / ".env.example").read_text()
        present = {
            line.split("=")[0]
            for line in env_text.splitlines()
            if "=" in line and not line.startswith("#")
        }
        missing = required - present
        assert not missing, f"Keys missing from .env.example: {missing}"

    def test_prometheus_config_valid(self):
        """prometheus.yml must be valid YAML with at least one scrape config."""
        data = yaml.safe_load((ROOT / "monitoring" / "prometheus.yml").read_text())
        assert "scrape_configs" in data, "prometheus.yml missing 'scrape_configs'"
        assert isinstance(data["scrape_configs"], list) and len(data["scrape_configs"]) > 0

    def test_alert_rules_valid(self):
        """alerts.yml must be valid YAML with at least one rule group."""
        data = yaml.safe_load((ROOT / "monitoring" / "alerts.yml").read_text())
        assert "groups" in data, "alerts.yml missing 'groups'"
        assert isinstance(data["groups"], list) and len(data["groups"]) > 0


@pytest.mark.smoke
class TestScriptSyntax:
    """Shell scripts must pass bash -n (no syntax errors)."""

    SCRIPTS = ["scripts/setup.sh", "scripts/update.sh", "scripts/backup.sh"]

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_script_syntax(self, script):
        r = _run(["bash", "-n", script])
        assert r.returncode == 0, f"{script} has syntax errors:\n{r.stderr}"

    @pytest.mark.parametrize("script", SCRIPTS)
    def test_script_is_executable(self, script):
        path = ROOT / script
        assert path.stat().st_mode & 0o111, f"{script} is not executable"


@pytest.mark.smoke
class TestAllServicesHealthy:
    """Protocol-native health checks — no docker CLI required."""

    def test_redis_healthy(self):
        import redis as redis_lib

        host = os.getenv("REDIS_HOST", "localhost")
        client = redis_lib.Redis(host=host, port=6379, socket_connect_timeout=5)
        assert client.ping(), "Redis did not respond to PING"

    def test_postgres_healthy(self, pg_conn):
        cur = pg_conn.cursor()
        cur.execute("SELECT 1")
        assert cur.fetchone()[0] == 1

    def test_neo4j_healthy(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("RETURN 1 AS n")
            assert result.single()["n"] == 1

    def test_qdrant_healthy(self, http):
        url = os.getenv("QDRANT_URL", "http://localhost:6333")
        r = http.get(f"{url}/healthz")
        assert r.status_code == 200
