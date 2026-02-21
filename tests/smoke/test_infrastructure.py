"""
Infrastructure validation tests — invokes shell checks as subprocesses.
These verify the compose/config files are correct before any service starts.
"""
import subprocess
import pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)


@pytest.mark.smoke
class TestComposeConfig:
    def test_compose_config_valid(self):
        """docker compose config must parse without errors."""
        r = _run(["docker", "compose", "config", "--quiet"])
        assert r.returncode == 0, f"docker compose config failed:\n{r.stderr}"

    def test_no_latest_image_tags(self):
        """All images must be pinned to explicit versions — no :latest."""
        compose = (ROOT / "docker-compose.yml").read_text()
        import re
        latest_lines = [
            line.strip() for line in compose.splitlines()
            if re.search(r"image:.*:latest", line)
        ]
        assert not latest_lines, f"Found :latest tags:\n" + "\n".join(latest_lines)

    def test_no_deploy_resources_blocks(self):
        """deploy.resources.limits is Swarm-only and silently ignored — must not exist."""
        compose = (ROOT / "docker-compose.yml").read_text()
        assert "deploy:" not in compose, \
            "Found 'deploy:' in docker-compose.yml — use mem_limit/cpus instead"

    def test_env_example_has_all_required_keys(self):
        """Every key in .env.example must be documented."""
        required = {"POSTGRES_PASSWORD", "NEO4J_PASSWORD", "GRAFANA_PASSWORD"}
        env_text = (ROOT / ".env.example").read_text()
        present = {line.split("=")[0] for line in env_text.splitlines() if "=" in line and not line.startswith("#")}
        missing = required - present
        assert not missing, f"Keys missing from .env.example: {missing}"

    def test_prometheus_config_valid(self):
        """`promtool check config` via Docker — no host install required."""
        r = _run([
            "docker", "run", "--rm",
            "--entrypoint", "/bin/promtool",
            "-v", f"{ROOT}/monitoring:/etc/prometheus:ro",
            "prom/prometheus:v3.9.1",
            "check", "config", "/etc/prometheus/prometheus.yml",
        ])
        assert r.returncode == 0, f"promtool check config failed:\n{r.stderr}"

    def test_alert_rules_valid(self):
        """`promtool check rules` via Docker — no host install required."""
        r = _run([
            "docker", "run", "--rm",
            "--entrypoint", "/bin/promtool",
            "-v", f"{ROOT}/monitoring:/etc/prometheus:ro",
            "prom/prometheus:v3.9.1",
            "check", "rules", "/etc/prometheus/alerts.yml",
        ])
        assert r.returncode == 0, f"promtool check rules failed:\n{r.stderr}"


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
    INFRA_SERVICES = ["redis", "postgres", "neo4j", "qdrant"]

    @pytest.mark.parametrize("service", INFRA_SERVICES)
    def test_service_is_healthy(self, service):
        import json
        r = _run(["docker", "compose", "ps", "--format", "json", service])
        assert r.returncode == 0, f"docker compose ps failed for {service}:\n{r.stderr}"

        rows = [json.loads(line) for line in r.stdout.splitlines() if line.strip()]
        assert rows, f"No container data returned for service '{service}' — is it running?"

        for data in rows:
            health = data.get("Health", "")
            state = data.get("State", "")
            assert state == "running", f"{service} is not running (state={state})"
            assert health == "healthy", f"{service} is not healthy (health={health})"
