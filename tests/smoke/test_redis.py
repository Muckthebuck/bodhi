"""Smoke tests — Redis"""
import pytest


@pytest.mark.smoke
class TestRedis:
    def test_ping(self, redis_client):
        assert redis_client.ping()

    def test_set_get(self, redis_client):
        redis_client.set("bodhi:smoke", "ok", ex=10)
        assert redis_client.get("bodhi:smoke") == "ok"

    def test_delete(self, redis_client):
        redis_client.set("bodhi:smoke:del", "1", ex=10)
        redis_client.delete("bodhi:smoke:del")
        assert redis_client.get("bodhi:smoke:del") is None

    def test_server_info(self, redis_client):
        info = redis_client.info()
        assert info["redis_version"]
        assert info["connected_clients"] >= 1
