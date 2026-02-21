"""
Shared fixtures for Bodhi test suite.
Loads credentials from .env (production) with fallback to .env.test
(committed test defaults) so tests never fail due to a missing .env.

Service hostnames are configurable via environment variables so the
same test suite runs both locally (defaults → localhost) and inside
the Docker network (set via the test-runner service in docker-compose.dev.yml).
"""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

_ROOT = Path(__file__).parent.parent

# .env takes precedence; fall back to committed .env.test
if (_ROOT / ".env").exists():
    load_dotenv(_ROOT / ".env")
else:
    load_dotenv(_ROOT / "tests" / "files" / ".env.test")


# ── Connection details from env ───────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


# Infra hosts — override when running inside Docker network
_REDIS_HOST      = _env("REDIS_HOST",      "localhost")
_POSTGRES_HOST   = _env("POSTGRES_HOST",   "localhost")
_NEO4J_HOST      = _env("NEO4J_HOST",      "localhost")


@pytest.fixture(scope="session")
def pg_conn():
    import psycopg2
    conn = psycopg2.connect(
        host=_POSTGRES_HOST,
        port=5432,
        dbname="bodhi",
        user="bodhi",
        password=_env("POSTGRES_PASSWORD"),
    )
    yield conn
    conn.close()


@pytest.fixture(scope="session")
def redis_client():
    import redis as redis_lib
    client = redis_lib.Redis(host=_REDIS_HOST, port=6379, decode_responses=True)
    yield client
    client.close()


@pytest.fixture(scope="session")
def neo4j_driver():
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        f"bolt://{_NEO4J_HOST}:7687",
        auth=("neo4j", _env("NEO4J_PASSWORD")),
    )
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def http():
    """Requests session. Default timeout of 15s to handle NLU warm-up on first call."""
    s = requests.Session()
    s.request = lambda method, url, **kw: requests.Session.request(
        s, method, url, timeout=kw.pop("timeout", 15), **kw
    )
    yield s
    s.close()
