"""Smoke tests — Prometheus health and scrape config"""
import pytest


@pytest.mark.smoke
class TestPrometheus:
    BASE = "http://localhost:9090"
    EXPECTED_JOBS = {"node", "prometheus", "redis", "postgres", "loki"}

    def test_healthy(self, http):
        r = http.get(f"{self.BASE}/-/healthy")
        assert r.status_code == 200

    def test_ready(self, http):
        r = http.get(f"{self.BASE}/-/ready")
        assert r.status_code == 200

    def test_config_loaded(self, http):
        r = http.get(f"{self.BASE}/api/v1/status/config")
        assert r.status_code == 200
        assert r.json()["status"] == "success"

    def test_all_scrape_jobs_configured(self, http):
        r = http.get(f"{self.BASE}/api/v1/targets")
        assert r.status_code == 200
        active = r.json()["data"]["activeTargets"]
        jobs = {t["labels"]["job"] for t in active}
        missing = self.EXPECTED_JOBS - jobs
        assert not missing, f"Scrape jobs not found in Prometheus: {missing}"

    def test_alert_rules_loaded(self, http):
        r = http.get(f"{self.BASE}/api/v1/rules")
        assert r.status_code == 200
        groups = r.json()["data"]["groups"]
        assert len(groups) >= 1, "No alert rule groups loaded"
        rule_names = {rule["name"] for g in groups for rule in g["rules"]}
        assert "ServiceDown" in rule_names
        assert "HighMemoryUsage" in rule_names
        assert "RedisMemoryHigh" in rule_names
