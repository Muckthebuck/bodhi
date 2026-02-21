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

    def test_settings_required_keys(self, pg_conn):
        with pg_conn.cursor() as cur:
            cur.execute("SELECT key FROM settings")
            keys = {row[0] for row in cur.fetchall()}
        required = {"personality", "voice", "screen", "character"}
        missing = required - keys
        assert not missing, f"Missing settings keys: {missing}"

    def test_skill_executions_fk_enforced(self, pg_conn):
        """skill_executions.skill_id must reference skills.skill_id."""
        import psycopg2
        with pg_conn.cursor() as cur:
            try:
                cur.execute("""
                    INSERT INTO skill_executions (skill_id, status)
                    VALUES ('__nonexistent_skill__', 'success')
                """)
                pg_conn.rollback()
                assert False, "FK violation should have been raised"
            except psycopg2.errors.ForeignKeyViolation:
                pg_conn.rollback()  # expected — FK is enforced

    @pytest.mark.parametrize("table,col", [
        ("memories", "id"),
        ("skills", "id"),
        ("skill_executions", "id"),
        ("tool_permissions", "id"),
        ("tool_audit_log", "id"),
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
