"""Smoke tests — Loki log ingestion endpoint"""

import os
import time

import pytest


@pytest.mark.smoke
class TestLoki:
    BASE = os.getenv("LOKI_URL", "http://localhost:3100")

    def test_ready(self, http):
        # Loki's /ready returns 503 while the ingester ring initialises.
        # Retry for up to 30 s before failing.
        deadline = time.time() + 30
        while True:
            r = http.get(f"{self.BASE}/ready")
            if r.status_code == 200:
                break
            if time.time() >= deadline:
                raise AssertionError(
                    f"Loki /ready still returning {r.status_code} after 30 s: {r.text[:200]}"
                )
            time.sleep(3)

    def test_metrics_endpoint(self, http):
        r = http.get(f"{self.BASE}/metrics")
        assert r.status_code == 200
        assert "loki_" in r.text

    def test_labels_endpoint(self, http):
        r = http.get(f"{self.BASE}/loki/api/v1/labels")
        assert r.status_code == 200
        assert r.json()["status"] == "success"
