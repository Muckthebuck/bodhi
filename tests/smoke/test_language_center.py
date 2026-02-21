"""Smoke tests — Language Center"""
import pytest


BASE = "http://localhost:8002"


@pytest.mark.smoke
class TestLanguageCenterHealth:
    def test_health_status(self, http):
        r = http.get(f"{BASE}/health")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "healthy"
        assert body["agent"] == "language-center"

    def test_health_has_model_loaded_field(self, http):
        r = http.get(f"{BASE}/health")
        assert "model_loaded" in r.json()

    def test_metrics_endpoint(self, http):
        r = http.get(f"{BASE}/metrics")
        assert r.status_code == 200
        assert "bodhi_language_requests_total" in r.text
        assert "bodhi_intent_classified_total" in r.text


@pytest.mark.smoke
class TestLanguageCenterUnderstand:
    def test_understand_returns_intent(self, http):
        r = http.post(f"{BASE}/understand", json={
            "text": "hello there",
            "session_id": "smoke-test",
            "context": {},
        })
        assert r.status_code == 200
        body = r.json()
        assert "intent" in body
        assert "intent_confidence" in body
        assert 0.0 <= body["intent_confidence"] <= 1.0

    def test_understand_chitchat_intent(self, http):
        r = http.post(f"{BASE}/understand", json={
            "text": "how are you doing today?",
            "session_id": "smoke-test",
            "context": {},
        })
        assert r.status_code == 200
        assert r.json()["intent"] == "chitchat"

    def test_understand_system_status_intent(self, http):
        r = http.post(f"{BASE}/understand", json={
            "text": "how are you feeling?",
            "session_id": "smoke-test",
            "context": {},
        })
        assert r.status_code == 200
        assert r.json()["intent"] in ("system.status", "chitchat")

    def test_understand_returns_entities(self, http):
        r = http.post(f"{BASE}/understand", json={
            "text": "remind me tomorrow to call Alice",
            "session_id": "smoke-test",
            "context": {},
        })
        assert r.status_code == 200
        body = r.json()
        assert "entities" in body
        assert isinstance(body["entities"], list)

    def test_understand_returns_sentiment(self, http):
        r = http.post(f"{BASE}/understand", json={
            "text": "this is great!",
            "session_id": "smoke-test",
            "context": {},
        })
        assert r.status_code == 200
        body = r.json()
        assert body["sentiment"] in ("positive", "neutral", "negative")


@pytest.mark.smoke
class TestLanguageCenterGenerate:
    def test_generate_returns_text(self, http):
        r = http.post(f"{BASE}/generate", json={
            "prompt": "The user said hello",
            "intent": "chitchat",
            "emotion": {"valence": 0.5, "arousal": 0.3, "label": "happy"},
            "personality": {
                "openness": 0.8,
                "conscientiousness": 0.7,
                "extraversion": 0.5,
                "agreeableness": 0.8,
                "neuroticism": 0.2,
            },
            "max_tokens": 100,
            "temperature": 0.7,
        })
        assert r.status_code == 200
        body = r.json()
        assert "text" in body
        assert len(body["text"]) > 0
        assert "latency_ms" in body

    def test_generate_different_emotions_differ(self, http):
        happy = http.post(f"{BASE}/generate", json={
            "prompt": "The user greeted Bodhi",
            "intent": "chitchat",
            "emotion": {"valence": 0.9, "arousal": 0.7, "label": "excited"},
            "personality": {"openness": 0.8, "conscientiousness": 0.7,
                            "extraversion": 0.9, "agreeableness": 0.8, "neuroticism": 0.2},
            "max_tokens": 80,
        }).json()["text"]

        sad = http.post(f"{BASE}/generate", json={
            "prompt": "The user greeted Bodhi",
            "intent": "chitchat",
            "emotion": {"valence": -0.5, "arousal": 0.2, "label": "sad"},
            "personality": {"openness": 0.8, "conscientiousness": 0.7,
                            "extraversion": 0.3, "agreeableness": 0.8, "neuroticism": 0.7},
            "max_tokens": 80,
        }).json()["text"]

        assert happy != sad


@pytest.mark.smoke
class TestLanguageCenterSentiment:
    def test_sentiment_positive(self, http):
        r = http.post(f"{BASE}/sentiment", json={"text": "I love this, it's wonderful!"})
        assert r.status_code == 200
        body = r.json()
        assert body["label"] == "positive"
        assert 0.0 <= body["score"] <= 1.0

    def test_sentiment_negative(self, http):
        r = http.post(f"{BASE}/sentiment", json={"text": "I hate this, it's terrible."})
        assert r.status_code == 200
        assert r.json()["label"] == "negative"

    def test_sentiment_neutral(self, http):
        r = http.post(f"{BASE}/sentiment", json={"text": "The sky is blue."})
        assert r.status_code == 200
        assert r.json()["label"] in ("neutral", "positive", "negative")
