"""Smoke tests — Prometheus exporters (node, postgres, redis)"""
import pytest


@pytest.mark.smoke
class TestNodeExporter:
    BASE = "http://localhost:9100"

    def test_metrics_endpoint(self, http):
        r = http.get(f"{self.BASE}/metrics")
        assert r.status_code == 200

    def test_cpu_metric_present(self, http):
        r = http.get(f"{self.BASE}/metrics")
        assert "node_cpu_seconds_total" in r.text

    def test_memory_metric_present(self, http):
        r = http.get(f"{self.BASE}/metrics")
        assert "node_memory_MemTotal_bytes" in r.text

    def test_filesystem_metric_present(self, http):
        r = http.get(f"{self.BASE}/metrics")
        assert "node_filesystem_size_bytes" in r.text


@pytest.mark.smoke
class TestPrometheusTargetHealth:
    """Verify every configured scrape target is actively UP in Prometheus."""

    PROMETHEUS = "http://localhost:9090"
    EXPECTED_UP = {"node", "prometheus", "redis", "postgres", "loki"}

    def _targets_by_job(self, http) -> dict:
        r = http.get(f"{self.PROMETHEUS}/api/v1/targets")
        assert r.status_code == 200
        targets = r.json()["data"]["activeTargets"]
        return {t["labels"]["job"]: t["health"] for t in targets}

    @pytest.mark.parametrize("job", ["node", "prometheus", "redis", "postgres", "loki"])
    def test_target_is_up(self, http, job):
        by_job = self._targets_by_job(http)
        assert job in by_job, f"Prometheus has no active target for job '{job}'"
        assert by_job[job] == "up", (
            f"Prometheus target '{job}' is not up (health={by_job[job]})"
        )
