"""Smoke tests — Neo4j constraints, indexes, and seed data"""
import pytest


@pytest.mark.smoke
class TestNeo4j:
    def test_connection(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("RETURN 1 AS n")
            assert result.single()["n"] == 1

    def test_skill_id_constraint(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("""
                SHOW CONSTRAINTS
                YIELD name, type, labelsOrTypes, properties
                WHERE labelsOrTypes = ['Skill'] AND properties = ['skill_id']
                RETURN count(*) AS cnt
            """)
            assert result.single()["cnt"] >= 1, "Skill.skill_id uniqueness constraint missing"

    def test_category_name_constraint(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("""
                SHOW CONSTRAINTS
                YIELD labelsOrTypes, properties
                WHERE labelsOrTypes = ['Category'] AND properties = ['name']
                RETURN count(*) AS cnt
            """)
            assert result.single()["cnt"] >= 1, "Category.name constraint missing"

    def test_skill_categories_seeded(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (c:Category) RETURN count(c) AS cnt")
            cnt = result.single()["cnt"]
        assert cnt >= 7, f"Expected ≥7 categories, got {cnt}"

    def test_core_skills_seeded(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("MATCH (s:Skill) RETURN count(s) AS cnt")
            cnt = result.single()["cnt"]
        assert cnt >= 4, f"Expected ≥4 seed skills, got {cnt}"

    def test_skill_category_relationships(self, neo4j_driver):
        with neo4j_driver.session() as s:
            result = s.run("""
                MATCH (:Skill)-[:BELONGS_TO]->(:Category)
                RETURN count(*) AS cnt
            """)
            assert result.single()["cnt"] >= 1, "No Skill→Category relationships found"

    def test_skill_id_uniqueness_enforced(self, neo4j_driver):
        """Inserting two Skills with the same skill_id must raise a constraint error."""
        from neo4j.exceptions import ClientError
        with neo4j_driver.session() as s:
            s.run("CREATE (:Skill {skill_id: '__smoke_dup_test__', name: 'a'})")
            try:
                s.run("CREATE (:Skill {skill_id: '__smoke_dup_test__', name: 'b'})")
                assert False, "Expected uniqueness constraint violation"
            except ClientError as e:
                assert "ConstraintValidationFailed" in str(e) or "already exists" in str(e).lower()
            finally:
                s.run("MATCH (s:Skill {skill_id: '__smoke_dup_test__'}) DELETE s")
