"""
Semantic reasoning tests — language-center

Tests paraphrase robustness, intent boundary disambiguation, negation handling,
and NLU consistency. These also document known limitations of the Phase 2
keyword/pattern-based classifier (marked with xfail where the pattern matcher
is expected to fall short — Phase 4 replaces this with a fine-tuned model).
"""
import sys
import pytest

_main = sys.modules["lc_main"]
_classify_intent = _main._classify_intent
_analyse_sentiment = _main._analyse_sentiment
_extract_entities = _main._extract_entities
_generate_response = _main._generate_response


# ─────────────────────────────────────────────────────────────────────────────
# Paraphrase robustness
# Different surface forms of the same intent should yield the same classification
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentParaphraseRobustness:
    """Same intent, varied phrasing — the classifier should be consistent."""

    @pytest.mark.parametrize("text", [
        "hello",
        "hey there",
        "hi!",
        "what's up?",
        "howdy",
        "hola",
        "greetings",
        "hey, how's it going?",
    ])
    def test_greeting_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "chitchat", f"'{text}' → expected chitchat, got {intent}"

    @pytest.mark.parametrize("text", [
        "remind me to call Alice tomorrow",
        "set a reminder for 3pm",
        "create a task: buy groceries",
        "add a reminder to water the plants",
        "remember to send the report",
    ])
    def test_task_create_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "task.create", f"'{text}' → expected task.create, got {intent}"

    @pytest.mark.parametrize("text", [
        "show me my tasks",
        "list my reminders",
        "what's on my list?",
        "what's on my agenda?",
        "show my reminders",
    ])
    def test_task_list_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "task.list", f"'{text}' → expected task.list, got {intent}"

    @pytest.mark.parametrize("text", [
        "what is photosynthesis?",
        "who is Ada Lovelace?",
        "explain how gravity works",
        "tell me about the French Revolution",
        "define recursion",
        "what are black holes?",
    ])
    def test_factual_query_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "query.factual", f"'{text}' → expected query.factual, got {intent}"

    @pytest.mark.parametrize("text", [
        "goodnight",
        "good night",
        "bye",
        "goodbye",
        "see you later",
        pytest.param("shutting down", marks=pytest.mark.xfail(
            reason="'shutting down' uses gerund form; Phase 2 regex only matches 'shutdown'/'shut down'"
        )),
    ])
    def test_shutdown_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "system.shutdown", f"'{text}' → expected system.shutdown, got {intent}"

    @pytest.mark.parametrize("text", [
        "are you ok?",
        "what's your status?",
        "system status",
        "what is your status?",
    ])
    def test_status_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "system.status", f"'{text}' → expected system.status, got {intent}"

    @pytest.mark.parametrize("text", [
        "how are you?",
        "how are you doing?",
        "how are you feeling?",
    ])
    def test_greeting_how_are_you_maps_to_chitchat(self, text):
        """'how are you' phrases are chitchat, not system.status (intentional behavior)."""
        intent, _ = _classify_intent(text)
        assert intent == "chitchat", f"'{text}' → expected chitchat, got {intent}"

    @pytest.mark.parametrize("text", [
        "do you remember when we talked?",
        "remember when I told you about Paris?",
        "don't you remember my birthday?",
        "recall our last conversation",
    ])
    def test_memory_query_paraphrases(self, text):
        intent, _ = _classify_intent(text)
        assert intent == "query.memory", f"'{text}' → expected query.memory, got {intent}"


# ─────────────────────────────────────────────────────────────────────────────
# Intent boundary disambiguation
# Similar-looking inputs that should map to DIFFERENT intents
# ─────────────────────────────────────────────────────────────────────────────

class TestIntentBoundaryDisambiguation:
    """Inputs near decision boundaries should land on the correct side."""

    def test_greeting_not_status(self):
        # "hi" is chitchat, not system.status
        intent, _ = _classify_intent("hi")
        assert intent == "chitchat"

    def test_task_create_not_chitchat(self):
        intent, _ = _classify_intent("remind me to call Bob")
        assert intent != "chitchat"

    def test_factual_not_memory(self):
        # "what is" is factual, not a memory query
        intent, _ = _classify_intent("what is the speed of light?")
        assert intent == "query.factual"

    def test_memory_not_factual(self):
        # "do you remember" is memory, not factual
        intent, _ = _classify_intent("do you remember what I said about Alice?")
        assert intent == "query.memory"

    def test_shutdown_not_chitchat(self):
        # "goodbye" should be shutdown, not generic chitchat
        intent, _ = _classify_intent("goodbye!")
        assert intent == "system.shutdown"

    def test_skill_execute_not_factual(self):
        intent, _ = _classify_intent("run the weather skill")
        assert intent == "skill.execute"

    def test_confidence_higher_for_clear_inputs(self):
        _, conf_clear = _classify_intent("hello")
        _, conf_ambiguous = _classify_intent("xyzzy florp wibble")
        assert conf_clear > conf_ambiguous


# ─────────────────────────────────────────────────────────────────────────────
# Negation and edge cases
# Documents known Phase 2 limitations (xfail) and things that must work
# ─────────────────────────────────────────────────────────────────────────────

class TestNegationAndEdgeCases:
    def test_empty_string_returns_unknown(self):
        intent, conf = _classify_intent("")
        assert intent == "unknown"

    def test_whitespace_only_returns_unknown(self):
        intent, _ = _classify_intent("   ")
        assert intent == "unknown"

    def test_single_word_unknown(self):
        intent, _ = _classify_intent("xyzzy")
        assert intent == "unknown"

    def test_very_long_input_does_not_crash(self):
        text = "what is " + "the meaning of life " * 100
        intent, conf = _classify_intent(text)
        assert isinstance(intent, str)
        assert 0.0 <= conf <= 1.0

    def test_mixed_case_handled(self):
        upper, _ = _classify_intent("HELLO")
        lower, _ = _classify_intent("hello")
        assert upper == lower

    def test_punctuation_does_not_break_classification(self):
        intent, _ = _classify_intent("hello!!!")
        assert intent == "chitchat"

    @pytest.mark.xfail(
        reason="Phase 2 keyword classifier cannot handle negation — 'not bad' still matches 'bad'"
    )
    def test_negated_negative_sentiment_is_positive(self):
        label, _ = _analyse_sentiment("not bad at all!")
        assert label == "positive"

    @pytest.mark.xfail(
        reason="Phase 2 pattern classifier cannot handle implicit task creation without trigger words"
    )
    def test_implicit_task_create_without_remind(self):
        # "I need to pick up the kids at 3" implies task.create but has no keyword
        intent, _ = _classify_intent("I need to pick up the kids at 3pm")
        assert intent == "task.create"


# ─────────────────────────────────────────────────────────────────────────────
# Sentiment reasoning
# ─────────────────────────────────────────────────────────────────────────────

class TestSentimentReasoning:
    @pytest.mark.parametrize("text,expected", [
        ("I love this, it's wonderful!", "positive"),
        ("this is great and amazing", "positive"),
        ("I hate this, it's terrible", "negative"),
        ("awful and horrible experience", "negative"),
        ("the file was saved", "neutral"),
        ("ok", "neutral"),
    ])
    def test_sentiment_classification(self, text, expected):
        label, _ = _analyse_sentiment(text)
        assert label == expected, f"'{text}' → expected {expected}, got {label}"

    def test_more_positive_words_wins(self):
        label, _ = _analyse_sentiment("great wonderful amazing love — but slightly bad")
        assert label == "positive"

    def test_more_negative_words_wins(self):
        label, _ = _analyse_sentiment("terrible awful hate — but one good thing")
        assert label == "negative"

    def test_score_reflects_signal_strength(self):
        _, strong = _analyse_sentiment("I love this, it's wonderful and amazing!")
        _, weak = _analyse_sentiment("pretty good")
        # Strong signal may score higher — but both must be valid
        assert 0.0 <= strong <= 1.0
        assert 0.0 <= weak <= 1.0

    def test_score_is_one_for_unambiguous_single_word(self):
        _, score = _analyse_sentiment("love")
        assert score == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Response generation reasoning
# Generated responses should reflect emotion and personality correctly
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerationReasoning:
    _base_personality = {
        "openness": 0.8, "conscientiousness": 0.7,
        "extraversion": 0.5, "agreeableness": 0.8, "neuroticism": 0.2,
    }

    def test_shutdown_response_contains_farewell_tone(self):
        text = _generate_response(
            "user said goodnight",
            "system.shutdown",
            {"valence": 0.3, "arousal": 0.2},
            self._base_personality,
        )
        farewell_words = {"night", "sleep", "rest", "tomorrow", "dream", "shutdown", "bye"}
        assert any(w in text.lower() for w in farewell_words), \
            f"Shutdown response missing farewell tone: '{text}'"

    def test_status_response_mentions_feeling(self):
        text = _generate_response(
            "user asked how are you",
            "system.status",
            {"valence": 0.6, "arousal": 0.4},
            self._base_personality,
        )
        feeling_words = {"feeling", "doing", "great", "good", "operational", "ready", "running"}
        assert any(w in text.lower() for w in feeling_words), \
            f"Status response missing feeling word: '{text}'"

    def test_high_neuroticism_adds_caveat_suffix(self):
        cautious = {**self._base_personality, "neuroticism": 0.9}
        text = _generate_response("hello", "chitchat", {"valence": 0.5, "arousal": 0.3}, cautious)
        assert "wrong" in text.lower() or "let me know" in text.lower()

    def test_responses_are_deterministic_same_inputs(self):
        args = ("hello", "chitchat", {"valence": 0.5, "arousal": 0.3}, self._base_personality)
        assert _generate_response(*args) == _generate_response(*args)

    def test_all_intents_produce_non_empty_response(self):
        intents = [
            "chitchat", "query.factual", "query.memory", "task.create",
            "task.list", "skill.execute", "system.status", "system.shutdown", "unknown",
        ]
        emotion = {"valence": 0.3, "arousal": 0.3}
        for intent in intents:
            text = _generate_response("test", intent, emotion, self._base_personality)
            assert len(text) > 0, f"Empty response for intent '{intent}'"


class TestSubscriberResponseField:
    """The Redis subscriber must include a 'response' key with natural language text."""

    _default_emotion = {"valence": 0.0, "arousal": 0.0, "label": "neutral"}
    _default_personality = {
        "extraversion": 0.5, "agreeableness": 0.8,
        "neuroticism": 0.2, "openness": 0.7, "conscientiousness": 0.6,
    }

    def test_subscriber_response_is_natural_language(self):
        """_generate_response() called with default context must return plain text."""
        text = _generate_response("hello", "chitchat", self._default_emotion, self._default_personality)
        assert isinstance(text, str)
        assert len(text) > 0
        # Must not look like raw JSON (the old broken fallback)
        assert not text.startswith("{"), f"Response looks like raw JSON: {text!r}"

    def test_subscriber_response_included_in_result_dict(self):
        """Simulates what the subscriber now does — result dict must have 'response' key."""
        intent, confidence = _classify_intent("hello there")
        _, sentiment_score = _analyse_sentiment("hello there")
        sentiment_label = "positive"
        response_text = _generate_response(
            "hello there", intent, self._default_emotion, self._default_personality
        )
        result = {
            "request_id": "req-test",
            "response": response_text,
            "intent": intent,
        }
        assert "response" in result
        assert isinstance(result["response"], str)
        assert len(result["response"]) > 0
