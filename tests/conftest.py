"""
Shared fixtures for Bodhi test suite.
Loads .env from project root so tests can run against a live stack.
"""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (one level up from tests/)
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")


# ── Connection details from env ───────────────────────────────────────────────

def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


@pytest.fixture(scope="session")
def pg_conn():
    import psycopg2
    conn = psycopg2.connect(
        host="localhost",
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
    client = redis_lib.Redis(host="localhost", port=6379, decode_responses=True)
    yield client
    client.close()


@pytest.fixture(scope="session")
def neo4j_driver():
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", _env("NEO4J_PASSWORD")),
    )
    yield driver
    driver.close()


@pytest.fixture(scope="session")
def http():
    """Thin requests session with a short timeout."""
    s = requests.Session()
    s.request = lambda method, url, **kw: requests.Session.request(
        s, method, url, timeout=kw.pop("timeout", 5), **kw
    )
    yield s
    s.close()
