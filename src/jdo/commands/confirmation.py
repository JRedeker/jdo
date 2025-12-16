"""Confirmation matching system for user responses.

Uses fuzzy matching to interpret user responses to confirmation prompts,
supporting variations like "yes", "yeah", "yep", "sure", "ok" for confirmation
and "no", "nope", "cancel", "stop" for cancellation.
"""

from enum import Enum

from rapidfuzz import fuzz


class ConfirmationResult(str, Enum):
    """Result of matching a user response to a confirmation prompt."""

    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    UNCLEAR = "unclear"


class ConfirmationMatcher:
    """Matches user responses to confirmation prompts using fuzzy matching.

    Attributes:
        threshold: Minimum similarity score (0-100) for a fuzzy match.
    """

    # Words that indicate confirmation
    CONFIRM_WORDS: tuple[str, ...] = (
        "yes",
        "yeah",
        "yep",
        "yup",
        "sure",
        "ok",
        "okay",
        "y",
        "absolutely",
        "definitely",
        "correct",
        "right",
        "affirmative",
        "yess",  # Common typo
        "yas",  # Casual variation
    )

    # Words that indicate cancellation
    CANCEL_WORDS: tuple[str, ...] = (
        "no",
        "nope",
        "nah",
        "n",
        "cancel",
        "stop",
        "nevermind",
        "never",
        "abort",
        "quit",
        "negative",
        "dont",
        "don't",
    )

    def __init__(self, threshold: int = 80) -> None:
        """Initialize the confirmation matcher.

        Args:
            threshold: Minimum similarity score (0-100) for fuzzy matching.
                      Default is 80 (80% similarity required).
        """
        self.threshold = threshold

    def match(self, response: str) -> ConfirmationResult:
        """Match a user response to a confirmation result.

        Args:
            response: The user's response text.

        Returns:
            ConfirmationResult indicating whether the user confirmed,
            cancelled, or gave an unclear response.
        """
        # Normalize input
        normalized = response.strip().lower()

        if not normalized:
            return ConfirmationResult.UNCLEAR

        # Check for exact matches first (fast path)
        if normalized in self.CONFIRM_WORDS:
            return ConfirmationResult.CONFIRMED
        if normalized in self.CANCEL_WORDS:
            return ConfirmationResult.CANCELLED

        # Try fuzzy matching
        return self._fuzzy_match(normalized)

    def _fuzzy_match(self, normalized: str) -> ConfirmationResult:
        """Try fuzzy matching against confirmation and cancellation words.

        Args:
            normalized: The normalized (lowercase, trimmed) user response.

        Returns:
            ConfirmationResult based on fuzzy match scores.
        """
        confirm_score = self._best_fuzzy_score(normalized, self.CONFIRM_WORDS)
        cancel_score = self._best_fuzzy_score(normalized, self.CANCEL_WORDS)

        # If both are below threshold, it's unclear
        if confirm_score < self.threshold and cancel_score < self.threshold:
            return ConfirmationResult.UNCLEAR

        # Return whichever has the higher score (if above threshold)
        if confirm_score >= self.threshold and confirm_score >= cancel_score:
            return ConfirmationResult.CONFIRMED
        if cancel_score >= self.threshold:
            return ConfirmationResult.CANCELLED

        return ConfirmationResult.UNCLEAR

    def _best_fuzzy_score(self, text: str, candidates: tuple[str, ...]) -> float:
        """Find the best fuzzy match score against a list of candidates.

        Args:
            text: The text to match.
            candidates: Tuple of candidate strings to match against.

        Returns:
            The highest similarity score (0-100) among all candidates.
        """
        best_score = 0.0

        for candidate in candidates:
            # Use fuzz.ratio for simple similarity
            score = fuzz.ratio(text, candidate)
            best_score = max(best_score, score)

        return best_score
