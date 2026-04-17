"""
Tests for llm_cascade.confidence_scorer module.
Target coverage: >= 85%
"""

import pytest
from implement.llm_cascade.confidence_scorer import ConfidenceScorer
from implement.llm_cascade.enums import ConfidenceComponent


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def scorer():
    return ConfidenceScorer()


# ─────────────────────────────────────────────────────────────────────────────
# Initialization & Weights
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceScorerInit:
    """Tests for ConfidenceScorer initialization."""

    def test_default_weights(self, scorer):
        """Default weights should match ARCHITECTURE.md: 0.30/0.25/0.20/0.25."""
        assert scorer._weights[ConfidenceComponent.ENTROPY] == 0.30
        assert scorer._weights[ConfidenceComponent.REPETITION] == 0.25
        assert scorer._weights[ConfidenceComponent.LENGTH] == 0.20
        assert scorer._weights[ConfidenceComponent.PARSE_VALIDITY] == 0.25

    def test_weights_sum_to_one(self, scorer):
        total = sum(scorer._weights.values())
        assert abs(total - 1.0) < 1e-9

    def test_custom_weights(self):
        custom = {
            ConfidenceComponent.ENTROPY: 0.40,
            ConfidenceComponent.REPETITION: 0.20,
            ConfidenceComponent.LENGTH: 0.20,
            ConfidenceComponent.PARSE_VALIDITY: 0.20,
        }
        scorer = ConfidenceScorer(weights=custom)
        assert scorer._weights[ConfidenceComponent.ENTROPY] == 0.40

    def test_all_components_present(self, scorer):
        for comp in ConfidenceComponent:
            assert comp in scorer._weights


# ─────────────────────────────────────────────────────────────────────────────
# Overall Score
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceScorerScore:
    """Tests for overall confidence scoring."""

    def test_returns_float(self, scorer):
        result = scorer.score("Hello world")
        assert isinstance(result, float)

    def test_score_in_range_zero_to_one(self, scorer):
        # Test various inputs stay in valid range
        test_outputs = [
            "Hello world",
            "A" * 1000,
            '{"key": "value"}',
            "",
            "The quick brown fox jumps over the lazy dog",
        ]
        for output in test_outputs:
            score = scorer.score(output)
            assert 0.0 <= score <= 1.0, f"Score {score} out of range for: {output[:50]}"

    def test_empty_string_returns_low_score(self, scorer):
        """Empty string has 0 entropy score but other components score higher."""
        score = scorer.score("")
        # entropy=0, repetition=1 (short), length=0.2, parse_validity=0.8
        # = 0.30*0 + 0.25*1 + 0.20*0.2 + 0.25*0.8 = 0 + 0.25 + 0.04 + 0.2 = 0.49
        assert score < 0.6

    def test_whitespace_only_returns_low_score(self, scorer):
        """Whitespace-only text has low entropy but other components."""
        score = scorer.score("   \n\t  ")
        # entropy=0, repetition=1 (short), length=0.2, parse_validity=0.8
        # = 0.30*0 + 0.25*1 + 0.20*0.2 + 0.25*0.8 = 0.49
        assert score < 0.6

    def test_rounded_to_three_decimals(self, scorer):
        result = scorer.score("Some sample text for testing")
        # Verify it's rounded to 3 decimal places
        assert result == round(result, 3)

    def test_task_type_general(self, scorer):
        score = scorer.score("A normal paragraph of text.", task_type="general")
        assert 0.0 <= score <= 1.0

    def test_task_type_code(self, scorer):
        score = scorer.score("def hello():\n    return 'world'", task_type="code")
        assert 0.0 <= score <= 1.0

    def test_task_type_json(self, scorer):
        score = scorer.score('{"key": "value", "number": 42}', task_type="json")
        assert 0.0 <= score <= 1.0

    def test_task_type_xml(self, scorer):
        score = scorer.score("<root><child>value</child></root>", task_type="xml")
        assert 0.0 <= score <= 1.0

    def test_task_type_unknown(self, scorer):
        # Unknown task types should not crash
        score = scorer.score("text", task_type="unknown_type")
        assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Entropy Score
# ─────────────────────────────────────────────────────────────────────────────

class TestEntropyScore:
    """Tests for _entropy_score dimension."""

    def test_high_entropy_low_confidence(self, scorer):
        """Random-looking text has high entropy → low confidence score."""
        random_text = "xzqz aa bb cc dd ee ff gg hh ii jj kk ll mm nn oo pp"
        score = scorer._entropy_score(random_text)
        # High entropy → low score (inverted in _entropy_score)
        assert score < 0.5, "Random text should have low entropy confidence score"

    def test_low_entropy_high_confidence(self, scorer):
        """Repeated/common text has low entropy → high confidence score."""
        repeated = "hello " * 50
        score = scorer._entropy_score(repeated)
        assert score > 0.5, "Repeated text should have high entropy confidence score"

    def test_single_unique_token(self, scorer):
        """Single token returns 0.5 (not enough data)."""
        score = scorer._entropy_score("hello")
        assert score == 0.5

    def test_empty_string_returns_zero(self, scorer):
        score = scorer._entropy_score("")
        assert score == 0.0

    def test_whitespace_only_returns_zero(self, scorer):
        score = scorer._entropy_score("   \n  ")
        assert score == 0.0

    def test_normal_text_returns_moderate_score(self, scorer):
        """Normal English text has moderate entropy."""
        normal = "The quick brown fox jumps over the lazy dog. It was a sunny afternoon."
        score = scorer._entropy_score(normal)
        assert 0.0 < score <= 1.0

    def test_score_bounded_between_zero_and_one(self, scorer):
        texts = [
            "a b c d e f g h i j k l m n o p q r s t u v w x y z",
            "word word word word word word word",
            "The",
        ]
        for text in texts:
            score = scorer._entropy_score(text)
            assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Repetition Score
# ─────────────────────────────────────────────────────────────────────────────

class TestRepetitionScore:
    """Tests for _repetition_score dimension."""

    def test_no_repetition_high_score(self, scorer):
        """Normal text without repetition should score high."""
        text = "The quick brown fox jumps over the lazy dog."
        score = scorer._repetition_score(text)
        assert score == 1.0

    def test_repeated_phrase_low_score(self, scorer):
        """Text with repeated n-grams should score low."""
        text = "the cat the cat the cat the cat the cat the cat the cat"
        score = scorer._repetition_score(text)
        assert score < 1.0

    def test_short_text_returns_one(self, scorer):
        """Text < 50 chars too short to assess repetition."""
        text = "Hello world!"
        score = scorer._repetition_score(text)
        assert score == 1.0

    def test_minimal_repetition_below_threshold(self, scorer):
        """Repetition below 30% threshold should not penalize."""
        text = "word1 word2 word3 word1 word2 word3 word4 word5 word6 word7 word8 word9 word10"
        score = scorer._repetition_score(text)
        # Below 30% ratio should still be high
        assert score >= 0.5

    def test_code_like_repetition_low_score(self, scorer):
        """Code with repetition patterns should score low."""
        text = "error error error error error error error error error error"
        score = scorer._repetition_score(text)
        assert score < 0.5

    def test_diverse_text_high_score(self, scorer):
        """Diverse vocabulary should score high."""
        text = " ".join([f"token_{i}" for i in range(100)])
        score = scorer._repetition_score(text)
        assert score >= 0.5

    def test_score_bounded(self, scorer):
        for text in ["abc", "repeating repeating repeating", "x y z x y z x y z"]:
            score = scorer._repetition_score(text)
            assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Length Score
# ─────────────────────────────────────────────────────────────────────────────

class TestLengthScore:
    """Tests for _length_score dimension."""

    def test_empty_string_low_score_general(self, scorer):
        score = scorer._length_score("", task_type="general")
        assert score == 0.2  # < 20 chars

    def test_very_short_low_score_general(self, scorer):
        score = scorer._length_score("Hi", task_type="general")
        assert score == 0.2  # < 20 chars

    def test_short_but_ok_general(self, scorer):
        score = scorer._length_score("Hello world this is a short sentence.", task_type="general")
        assert score == 0.6  # < 100 chars

    def test_normal_length_high_score(self, scorer):
        text = "A" * 200
        score = scorer._length_score(text, task_type="general")
        assert score == 1.0

    def test_very_long_low_score(self, scorer):
        text = "A" * 60000
        score = scorer._length_score(text, task_type="general")
        assert score == 0.5  # > 50000 chars

    def test_code_very_short(self, scorer):
        score = scorer._length_score("x=1", task_type="code")
        assert score == 0.1  # < 10 chars

    def test_code_unclosed_block(self, scorer):
        text = "```python\nprint('hello')\nprint('world')"
        score = scorer._length_score(text, task_type="code")
        assert score == 0.5  # single code block marker

    def test_code_well_formed(self, scorer):
        text = "```python\nprint('hello')\n```\nprint('world')\n```"
        score = scorer._length_score(text, task_type="code")
        assert score == 1.0

    def test_json_very_short(self, scorer):
        score = scorer._length_score('"x"', task_type="json")
        assert score == 0.1  # < 5 chars

    def test_json_normal(self, scorer):
        score = scorer._length_score('{"key": "value"}', task_type="json")
        assert score == 1.0

    def test_xml_very_short(self, scorer):
        score = scorer._length_score("<a/>", task_type="xml")
        assert score == 0.1

    def test_xml_normal(self, scorer):
        score = scorer._length_score("<root><child>value</child></root>", task_type="xml")
        assert score == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Parse Validity Score
# ─────────────────────────────────────────────────────────────────────────────

class TestParseValidityScore:
    """Tests for _parse_validity_score dimension."""

    def test_valid_json_object_high_score(self, scorer):
        score = scorer._parse_validity_score('{"key": "value"}', task_type="json")
        assert score == 1.0

    def test_valid_json_array_high_score(self, scorer):
        score = scorer._parse_validity_score('[1, 2, 3]', task_type="json")
        assert score == 1.0

    def test_invalid_json_zero_score(self, scorer):
        score = scorer._parse_validity_score('{invalid json}', task_type="json")
        assert score == 0.0

    def test_malformed_json_low_score(self, scorer):
        score = scorer._parse_validity_score('{"key": missing_value}', task_type="json")
        assert score == 0.0

    def test_well_formed_code_block_score(self, scorer):
        """Even number of code block markers gives higher score."""
        text = "```python\nprint('hello')\n```\nprint('world')\n```\nprint('done')\n```"
        score = scorer._parse_validity_score(text, task_type="code")
        assert 0.8 <= score <= 0.95  # 4 backticks = 2 pairs → 0.9

    def test_unclosed_code_block_low_score(self, scorer):
        text = "```python\nprint('hello')"
        score = scorer._parse_validity_score(text, task_type="code")
        assert score == 0.3

    def test_single_code_block_marker_low_score(self, scorer):
        text = "Some text ```python code without closing"
        score = scorer._parse_validity_score(text, task_type="general")
        assert score == 0.3

    def test_xml_like_with_closing_tag_score(self, scorer):
        """XML with proper closing tags scores higher."""
        text = "<root><child>value</root>"
        score = scorer._parse_validity_score(text, task_type="xml")
        assert score >= 0.7  # has closing tag but nested

    def test_xml_well_formed_high_score(self, scorer):
        text = "<root><child>value</child></root>"
        score = scorer._parse_validity_score(text, task_type="xml")
        assert score >= 0.8

    def test_unstructured_text_moderate_score(self, scorer):
        text = "This is just regular prose without any structure."
        score = scorer._parse_validity_score(text, task_type="general")
        assert score == 0.8

    def test_stripped_whitespace(self, scorer):
        text = '  {"key": "value"}  '
        score = scorer._parse_validity_score(text, task_type="json")
        assert score == 1.0


# ─────────────────────────────────────────────────────────────────────────────
# Score Components
# ─────────────────────────────────────────────────────────────────────────────

class TestScoreComponents:
    """Tests for score_components debug method."""

    def test_returns_dict(self, scorer):
        result = scorer.score_components("Hello world")
        assert isinstance(result, dict)

    def test_all_components_present(self, scorer):
        result = scorer.score_components("test text")
        expected_keys = {"entropy", "repetition", "length", "parse_validity"}
        assert set(result.keys()) == expected_keys

    def test_all_values_floats(self, scorer):
        result = scorer.score_components("Hello world")
        for v in result.values():
            assert isinstance(v, float)

    def test_all_values_in_range(self, scorer):
        result = scorer.score_components("test")
        for v in result.values():
            assert 0.0 <= v <= 1.0

    def test_components_sum_to_weighted_total(self, scorer):
        """Components should reconstruct the overall score."""
        output = "The quick brown fox jumps over the lazy dog."
        result = scorer.score_components(output)
        expected = (
            result["entropy"] * 0.30
            + result["repetition"] * 0.25
            + result["length"] * 0.20
            + result["parse_validity"] * 0.25
        )
        overall = scorer.score(output)
        assert abs(expected - overall) < 0.001


# ─────────────────────────────────────────────────────────────────────────────
# Edge Cases
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceScorerEdgeCases:
    """Edge case tests for ConfidenceScorer."""

    def test_very_long_input(self, scorer):
        text = "word " * 10000
        score = scorer.score(text)
        assert 0.0 <= score <= 1.0

    def test_unicode_input(self, scorer):
        text = "你好世界مرحبا العالم🎉"
        score = scorer.score(text)
        assert 0.0 <= score <= 1.0

    def test_special_characters(self, scorer):
        text = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        score = scorer.score(text)
        assert 0.0 <= score <= 1.0

    def test_newlines_and_tabs(self, scorer):
        text = "line1\nline2\tline3\r\nline4"
        score = scorer.score(text)
        assert 0.0 <= score <= 1.0

    def test_multiple_task_types_same_output(self, scorer):
        output = '{"key": "value"}'
        for task_type in ["general", "code", "json", "xml"]:
            score = scorer.score(output, task_type=task_type)
            assert 0.0 <= score <= 1.0