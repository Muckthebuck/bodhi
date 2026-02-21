"""Unit tests — language-center pure logic (no I/O)"""
import sys
import pytest

_main = sys.modules["lc_main"]
_templates = sys.modules["lc_templates"]

_classify_intent = _main._classify_intent
_extract_entities = _main._extract_entities
_analyse_sentiment = _main._analyse_sentiment
_generate_response = _main._generate_response
_personality_tone = _main._personality_tone
_select_template = _main._select_template
_render_template = _main._render_template
valence_to_adjective = _templates.valence_to_adjective
TEMPLATES = _templates.TEMPLATES


class TestClassifyIntent:
    def test_chitchat_hello(self):
        intent, conf = _classify_intent("hello there")
        assert intent == "chitchat"
        assert conf > 0.5

    def test_chitchat_hey(self):
        assert _classify_intent("hey, what's up?")[0] == "chitchat"

    def test_task_create_remind(self):
        assert _classify_intent("remind me to call Alice tomorrow")[0] == "task.create"

    def test_task_create_set_reminder(self):
        assert _classify_intent("set a reminder for 3pm")[0] == "task.create"

    def test_task_list(self):
        assert _classify_intent("show me my tasks")[0] == "task.list"

    def test_query_factual_what_is(self):
        assert _classify_intent("what is the capital of France?")[0] == "query.factual"

    def test_query_factual_explain(self):
        assert _classify_intent("explain quantum entanglement")[0] == "query.factual"

    def test_query_memory(self):
        assert _classify_intent("do you remember when we talked about Paris?")[0] == "query.memory"

    def test_system_status(self):
        assert _classify_intent("what is your status?")[0] == "system.status"

    def test_system_shutdown_goodnight(self):
        assert _classify_intent("goodnight")[0] == "system.shutdown"

    def test_system_shutdown_bye(self):
        assert _classify_intent("goodbye, see you tomorrow")[0] == "system.shutdown"

    def test_skill_execute(self):
        assert _classify_intent("run the backup skill")[0] == "skill.execute"

    def test_unknown_fallback(self):
        intent, conf = _classify_intent("xyzzy gibberish florp")
        assert intent == "unknown"
        assert conf < 0.5

    def test_confidence_is_float_in_range(self):
        for text in ["hello", "what is 2+2?", "gibberish"]:
            _, conf = _classify_intent(text)
            assert 0.0 <= conf <= 1.0


class TestExtractEntities:
    def test_extracts_date(self):
        entities = _extract_entities("remind me on 12/25/2025 to wrap gifts")
        types = [e["type"] for e in entities]
        assert "DATE" in types

    def test_extracts_time(self):
        entities = _extract_entities("meeting at 3:30pm")
        types = [e["type"] for e in entities]
        assert "TIME" in types

    def test_extracts_person_name(self):
        entities = _extract_entities("my name is Alice")
        types = [e["type"] for e in entities]
        assert "PERSON" in types

    def test_person_value_correct(self):
        entities = _extract_entities("my name is Alice")
        persons = [e["value"] for e in entities if e["type"] == "PERSON"]
        assert "Alice" in persons

    def test_no_entities_in_plain_text(self):
        entities = _extract_entities("the sky is blue")
        assert entities == []

    def test_multiple_entity_types(self):
        entities = _extract_entities("I'm Alice, meeting at 9am on 01/15/2025")
        types = {e["type"] for e in entities}
        assert len(types) >= 2

    def test_returns_list(self):
        assert isinstance(_extract_entities("hello"), list)


class TestAnalyseSentiment:
    def test_positive_text(self):
        label, score = _analyse_sentiment("I love this, it's wonderful and amazing!")
        assert label == "positive"
        assert score > 0.5

    def test_negative_text(self):
        label, score = _analyse_sentiment("I hate this, it's terrible and awful")
        assert label == "negative"
        assert score > 0.5

    def test_neutral_text(self):
        label, _ = _analyse_sentiment("the file was saved to disk")
        assert label == "neutral"

    def test_mixed_leans_positive(self):
        label, _ = _analyse_sentiment("great and wonderful but slightly bad")
        assert label == "positive"

    def test_score_always_in_range(self):
        for text in ["I love it", "I hate it", "neutral stuff"]:
            _, score = _analyse_sentiment(text)
            assert 0.0 <= score <= 1.0


class TestPersonalityTone:
    def test_high_extraversion_verbose(self):
        tone = _personality_tone({"extraversion": 0.9, "agreeableness": 0.8, "neuroticism": 0.2})
        assert tone["verbose"] is True

    def test_low_extraversion_not_verbose(self):
        tone = _personality_tone({"extraversion": 0.3, "agreeableness": 0.5, "neuroticism": 0.2})
        assert tone["verbose"] is False

    def test_high_neuroticism_cautious(self):
        tone = _personality_tone({"extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.8})
        assert tone["caution"] is True

    def test_low_neuroticism_not_cautious(self):
        tone = _personality_tone({"extraversion": 0.5, "agreeableness": 0.5, "neuroticism": 0.2})
        assert tone["caution"] is False

    def test_warmth_in_range(self):
        tone = _personality_tone({"extraversion": 0.5, "agreeableness": 0.8, "neuroticism": 0.2})
        assert 0.0 <= tone["warmth"] <= 1.0


class TestSelectTemplate:
    def test_returns_string(self):
        p = {"extraversion": 0.5, "agreeableness": 0.8, "neuroticism": 0.2}
        assert isinstance(_select_template("chitchat", p), str)

    def test_high_extraversion_picks_later_template(self):
        high_e = {"extraversion": 0.99}
        low_e = {"extraversion": 0.01}
        pool = TEMPLATES["chitchat"]
        hi_idx = int(0.99 * (len(pool) - 1))
        lo_idx = int(0.01 * (len(pool) - 1))
        assert _select_template("chitchat", high_e) == pool[hi_idx]
        assert _select_template("chitchat", low_e) == pool[lo_idx]

    def test_unknown_intent_uses_fallback(self):
        p = {"extraversion": 0.5}
        result = _select_template("nonexistent.intent", p)
        assert result in TEMPLATES["unknown"]


class TestRenderTemplate:
    def test_replaces_name(self):
        result = _render_template("Hello {name}!", name="Alice")
        assert "Alice" in result
        assert "{name}" not in result

    def test_replaces_emotion_adj(self):
        result = _render_template("Feeling {emotion_adj} today", emotion_adj="great")
        assert "great" in result

    def test_replaces_topic(self):
        result = _render_template("About {topic}:", topic="Python")
        assert "Python" in result

    def test_all_placeholders_replaced(self):
        template = "{name} {topic} {task} {count} {emotion_adj}"
        result = _render_template(template, name="A", topic="B", task="C", count=3, emotion_adj="D")
        assert "{" not in result

    def test_defaults_used_when_no_kwargs(self):
        result = _render_template("Hey {name}!")
        assert "{name}" not in result


class TestValenceToAdjective:
    def test_very_positive(self):
        assert valence_to_adjective(0.9) == "wonderful"

    def test_moderately_positive(self):
        assert valence_to_adjective(0.5) in ("good", "great")

    def test_neutral(self):
        assert valence_to_adjective(0.1) in ("okay", "neutral")

    def test_negative(self):
        adj = valence_to_adjective(-0.5)
        assert adj in ("concerned", "worried", "troubled", "a bit unsure")

    def test_very_negative(self):
        assert valence_to_adjective(-1.0) == "troubled"

    def test_returns_string(self):
        for v in [-1.0, -0.5, 0.0, 0.5, 1.0]:
            assert isinstance(valence_to_adjective(v), str)


class TestGenerateResponse:
    _personality = {
        "openness": 0.8, "conscientiousness": 0.7,
        "extraversion": 0.5, "agreeableness": 0.8, "neuroticism": 0.2,
    }

    def test_returns_non_empty_string(self):
        text = _generate_response("hello", "chitchat", {"valence": 0.5, "arousal": 0.3}, self._personality)
        assert isinstance(text, str)
        assert len(text) > 0

    def test_high_neuroticism_adds_caveat(self):
        cautious_personality = {**self._personality, "neuroticism": 0.8}
        text = _generate_response("hello", "chitchat", {"valence": 0.5, "arousal": 0.3}, cautious_personality)
        assert "wrong" in text.lower() or "let me know" in text.lower()

    def test_low_neuroticism_no_caveat(self):
        text = _generate_response("hello", "chitchat", {"valence": 0.5, "arousal": 0.3}, self._personality)
        assert "wrong" not in text.lower()

    def test_different_intents_differ(self):
        emotion = {"valence": 0.5, "arousal": 0.3}
        chitchat = _generate_response("hello", "chitchat", emotion, self._personality)
        status = _generate_response("hello", "system.status", emotion, self._personality)
        assert chitchat != status
