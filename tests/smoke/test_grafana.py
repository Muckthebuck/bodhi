"""Smoke tests — Grafana health and provisioning"""
import os
import pytest


@pytest.mark.smoke
class TestGrafana:
    BASE = os.getenv("GRAFANA_URL", "http://localhost:3000")

    @pytest.fixture(scope="class")
    def auth(self):
        password = os.environ.get("GRAFANA_PASSWORD", "admin")
        return ("admin", password)

    def test_health(self, http):
        r = http.get(f"{self.BASE}/api/health")
        assert r.status_code == 200
        body = r.json()
        assert body["database"] == "ok"

    def test_prometheus_datasource_provisioned(self, http, auth):
        r = http.get(f"{self.BASE}/api/datasources", auth=auth)
        assert r.status_code == 200
        names = {ds["name"] for ds in r.json()}
        assert "Prometheus" in names, f"Prometheus datasource not provisioned; found: {names}"

    def test_loki_datasource_provisioned(self, http, auth):
        r = http.get(f"{self.BASE}/api/datasources", auth=auth)
        assert r.status_code == 200
        names = {ds["name"] for ds in r.json()}
        assert "Loki" in names, f"Loki datasource not provisioned; found: {names}"

    def test_version_header_present(self, http):
        r = http.get(f"{self.BASE}/api/health")
        assert "version" in r.json()
