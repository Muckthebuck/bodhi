"""Smoke tests — PostgreSQL schema and data integrity"""
import pytest


@pytest.mark.smoke
class TestPostgres:
    EXPECTED_TABLES = {
        "memories", "skills", "skill_executions",
        "tool_permissions", "tool_audit_log", "settings", "conversations",
    }

    def test_connection(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone()[0] == 1

    def test_pgcrypto_extension(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("SELECT extname FROM pg_extension WHERE extname = 'pgcrypto'")
            assert cur.fetchone() is not None, "pgcrypto extension not installed"

    def test_all_tables_exist(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            """)
            tables = {row[0] for row in cur.fetchall()}
        assert self.EXPECTED_TABLES <= tables, f"Missing tables: {self.EXPECTED_TABLES - tables}"

    def test_gen_random_uuid(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("SELECT gen_random_uuid()")
            result = cur.fetchone()[0]
            assert result is not None

    def test_default_settings_seeded(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM settings")
            count = cur.fetchone()[0]
        assert count > 0, "settings table is empty — seed data missing"

    @pytest.mark.parametrize("table,col", [
        ("memories", "id"),
        ("skills", "id"),
        ("conversations", "id"),
    ])
    def test_uuid_primary_keys(self, pg_conn, table, col):
        with pg_conn.cursor() as cur:
            cur.execute(f"""
                SELECT data_type FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s
            """, (table, col))
            row = cur.fetchone()
        assert row is not None
        assert row[0] == "uuid", f"{table}.{col} is not UUID type"
