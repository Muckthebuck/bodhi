"""
Semantic memory tests — memory-manager (requires running stack)

Tests that the sentence-transformer embedding + Qdrant retrieval pipeline
actually understands meaning: paraphrased queries should still find the
right memories, and more relevant results should rank above irrelevant ones.
"""
import os
import pytest
import time


BASE = os.getenv("MEMORY_MANAGER_URL", "http://localhost:8001")
SESSION = "smoke-semantic"


@pytest.fixture(scope="module")
def seeded_memories(http):
    """Store a set of facts once; all tests in this module use them."""
    facts = [
        {
            "content": "The user prefers dark mode for all applications",
            "memory_type": "semantic",
            "importance": 0.9,
            "session_id": SESSION,
            "metadata": {"category": "ui_preference"},
        },
        {
            "content": "The user dislikes loud notification sounds",
            "memory_type": "semantic",
            "importance": 0.8,
            "session_id": SESSION,
            "metadata": {"category": "audio_preference"},
        },
        {
            "content": "The user's favourite programming language is Python",
            "memory_type": "semantic",
            "importance": 0.85,
            "session_id": SESSION,
            "metadata": {"category": "technical_preference"},
        },
        {
            "content": "The user goes to the gym every Monday and Thursday",
            "memory_type": "semantic",
            "importance": 0.7,
            "session_id": SESSION,
            "metadata": {"category": "routine"},
        },
        {
            "content": "The user has a cat named Miso",
            "memory_type": "semantic",
            "importance": 0.75,
            "session_id": SESSION,
            "metadata": {"category": "personal"},
        },
    ]
    for fact in facts:
        r = http.post(f"{BASE}/store", json=fact, timeout=30)
        assert r.status_code == 200, f"Failed to seed: {fact['content']}"

    # Give Qdrant a moment to index
    time.sleep(1)
    return facts


@pytest.mark.smoke
class TestSemanticRetrieval:
    """Paraphrased queries should retrieve the semantically correct memory."""

    def test_dark_mode_found_by_display_query(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "display brightness and colour scheme settings",
            "limit": 3,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        assert len(memories) > 0
        top_content = memories[0]["content"].lower()
        assert "dark" in top_content or "mode" in top_content or "prefer" in top_content

    def test_python_found_by_coding_query(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "what coding language does the user like?",
            "limit": 3,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        assert len(memories) > 0
        contents = " ".join(m["content"].lower() for m in memories[:2])
        assert "python" in contents or "programming" in contents or "language" in contents

    def test_gym_found_by_exercise_query(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "when does the user exercise?",
            "limit": 3,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        assert len(memories) > 0
        contents = " ".join(m["content"].lower() for m in memories[:2])
        assert "gym" in contents or "monday" in contents or "thursday" in contents

    def test_cat_found_by_pet_query(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "does the user have any pets?",
            "limit": 3,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        assert len(memories) > 0
        contents = " ".join(m["content"].lower() for m in memories[:2])
        assert "cat" in contents or "miso" in contents or "pet" in contents


@pytest.mark.smoke
class TestSemanticRanking:
    """More semantically relevant results should rank above irrelevant ones."""

    def test_relevant_ranks_above_irrelevant(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "user interface appearance preferences",
            "limit": 5,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        assert len(memories) >= 2

        # Dark mode should rank above gym schedule for a UI query
        dark_mode_rank = next(
            (i for i, m in enumerate(memories) if "dark" in m["content"].lower()), None
        )
        gym_rank = next(
            (i for i, m in enumerate(memories) if "gym" in m["content"].lower()), None
        )
        if dark_mode_rank is not None and gym_rank is not None:
            assert dark_mode_rank < gym_rank, \
                "Dark mode should rank above gym schedule for a UI appearance query"

    def test_similarity_scores_descending(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "personal preferences and habits",
            "limit": 5,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        if len(memories) >= 2:
            scores = [m.get("similarity", 1.0) for m in memories]
            for i in range(len(scores) - 1):
                assert scores[i] >= scores[i + 1] - 0.01, \
                    f"Score not descending: {scores}"

    def test_unrelated_query_low_scores(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "quantum physics and thermodynamics",
            "limit": 5,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        # All results should have low similarity for a completely unrelated query
        for m in memories:
            score = m.get("similarity", 0.0)
            assert score < 0.9, \
                f"Unexpectedly high similarity ({score}) for unrelated query"


@pytest.mark.smoke
class TestSemanticMinScoreFiltering:
    def test_high_min_score_filters_irrelevant(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "quantum physics equations",
            "limit": 5,
            "min_score": 0.8,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        memories = r.json()
        # Nothing in our seed set should be highly similar to quantum physics
        for m in memories:
            assert m.get("similarity", 0.0) >= 0.8

    def test_zero_min_score_returns_results(self, http, seeded_memories):
        r = http.post(f"{BASE}/retrieve", json={
            "query": "something the user likes",
            "limit": 3,
            "min_score": 0.0,
            "memory_type": "all",
        }, timeout=30)
        assert r.status_code == 200
        assert len(r.json()) > 0
