"""Tests for the confirmation matching system.

The confirmation system uses fuzzy matching to interpret user responses
to confirmation prompts (yes/no questions).
"""

import pytest


class TestConfirmationMatcher:
    """Tests for ConfirmationMatcher."""

    def test_yes_confirms(self) -> None:
        """Test: 'yes' confirms pending action."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("yes")

        assert result == ConfirmationResult.CONFIRMED

    def test_yeah_confirms_fuzzy(self) -> None:
        """Test: 'yeah' confirms via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("yeah")

        assert result == ConfirmationResult.CONFIRMED

    def test_yep_confirms_fuzzy(self) -> None:
        """Test: 'yep' confirms via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("yep")

        assert result == ConfirmationResult.CONFIRMED

    def test_sure_confirms_fuzzy(self) -> None:
        """Test: 'sure' confirms via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("sure")

        assert result == ConfirmationResult.CONFIRMED

    def test_ok_confirms_fuzzy(self) -> None:
        """Test: 'ok' confirms via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("ok")

        assert result == ConfirmationResult.CONFIRMED

    def test_okay_confirms_fuzzy(self) -> None:
        """Test: 'okay' confirms via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("okay")

        assert result == ConfirmationResult.CONFIRMED

    def test_y_confirms(self) -> None:
        """Test: 'y' confirms."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("y")

        assert result == ConfirmationResult.CONFIRMED

    def test_no_cancels(self) -> None:
        """Test: 'no' cancels via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("no")

        assert result == ConfirmationResult.CANCELLED

    def test_nope_cancels_fuzzy(self) -> None:
        """Test: 'nope' cancels via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("nope")

        assert result == ConfirmationResult.CANCELLED

    def test_cancel_cancels_fuzzy(self) -> None:
        """Test: 'cancel' cancels via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("cancel")

        assert result == ConfirmationResult.CANCELLED

    def test_stop_cancels_fuzzy(self) -> None:
        """Test: 'stop' cancels via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("stop")

        assert result == ConfirmationResult.CANCELLED

    def test_n_cancels(self) -> None:
        """Test: 'n' cancels."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("n")

        assert result == ConfirmationResult.CANCELLED

    def test_nevermind_cancels_fuzzy(self) -> None:
        """Test: 'nevermind' cancels via fuzzy match."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("nevermind")

        assert result == ConfirmationResult.CANCELLED

    def test_ambiguous_response_returns_unclear(self) -> None:
        """Test: Ambiguous response prompts for clarity."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("maybe")

        assert result == ConfirmationResult.UNCLEAR

    def test_random_text_returns_unclear(self) -> None:
        """Test: Random text returns unclear."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("the quick brown fox")

        assert result == ConfirmationResult.UNCLEAR

    def test_empty_string_returns_unclear(self) -> None:
        """Test: Empty string returns unclear."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        result = matcher.match("")

        assert result == ConfirmationResult.UNCLEAR

    def test_fuzzy_threshold_is_80_percent(self) -> None:
        """Test: Fuzzy threshold is 80% similarity."""
        from jdo.commands.confirmation import ConfirmationMatcher

        matcher = ConfirmationMatcher()
        assert matcher.threshold == 80

    def test_case_insensitive(self) -> None:
        """Test: Matching is case insensitive."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()

        assert matcher.match("YES") == ConfirmationResult.CONFIRMED
        assert matcher.match("Yes") == ConfirmationResult.CONFIRMED
        assert matcher.match("NO") == ConfirmationResult.CANCELLED
        assert matcher.match("No") == ConfirmationResult.CANCELLED

    def test_whitespace_trimmed(self) -> None:
        """Test: Whitespace is trimmed."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()

        assert matcher.match("  yes  ") == ConfirmationResult.CONFIRMED
        assert matcher.match("  no  ") == ConfirmationResult.CANCELLED

    def test_typo_yes_still_matches(self) -> None:
        """Test: Minor typos in 'yes' still match if above threshold."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()
        # "ues" is close enough to "yes" (2/3 characters match)
        # But actually rapidfuzz ratio("ues", "yes") = 67, below 80
        # "yess" should work though
        result = matcher.match("yess")

        assert result == ConfirmationResult.CONFIRMED

    def test_affirmative_variations(self) -> None:
        """Test: Various affirmative responses work."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()

        affirmatives = ["yes", "yep", "yeah", "sure", "ok", "okay", "y", "absolutely", "definitely"]
        for word in affirmatives:
            result = matcher.match(word)
            assert result == ConfirmationResult.CONFIRMED, f"'{word}' should confirm"

    def test_negative_variations(self) -> None:
        """Test: Various negative responses work."""
        from jdo.commands.confirmation import ConfirmationMatcher, ConfirmationResult

        matcher = ConfirmationMatcher()

        negatives = ["no", "nope", "n", "cancel", "stop", "nevermind", "nah"]
        for word in negatives:
            result = matcher.match(word)
            assert result == ConfirmationResult.CANCELLED, f"'{word}' should cancel"


class TestConfirmationResult:
    """Tests for ConfirmationResult enum."""

    def test_has_confirmed_value(self) -> None:
        """Test: ConfirmationResult has CONFIRMED value."""
        from jdo.commands.confirmation import ConfirmationResult

        assert hasattr(ConfirmationResult, "CONFIRMED")

    def test_has_cancelled_value(self) -> None:
        """Test: ConfirmationResult has CANCELLED value."""
        from jdo.commands.confirmation import ConfirmationResult

        assert hasattr(ConfirmationResult, "CANCELLED")

    def test_has_unclear_value(self) -> None:
        """Test: ConfirmationResult has UNCLEAR value."""
        from jdo.commands.confirmation import ConfirmationResult

        assert hasattr(ConfirmationResult, "UNCLEAR")
