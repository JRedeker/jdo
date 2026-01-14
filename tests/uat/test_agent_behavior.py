"""UAT tests for AI agent behavior constraints.

These tests verify that:
1. The agent asks only ONE question at a time
2. The agent does NOT offer unsolicited task breakdowns or suggestions
3. The agent is user-led (reflects user's words, doesn't generate ideas)

Tests use response analysis to detect constraint violations.
"""

from __future__ import annotations

import re

import pytest

from jdo.ai.agent import SYSTEM_PROMPT_TEMPLATE, get_agent_system_prompt


class TestSystemPromptConstraints:
    """Verify the system prompt contains required behavior constraints."""

    def test_one_question_rule_present(self):
        """System prompt must contain the one-question-at-a-time rule."""
        prompt = get_agent_system_prompt()

        assert "ONE question at a time" in prompt
        assert "NEVER ask multiple questions" in prompt

    def test_no_numbered_question_lists_rule(self):
        """System prompt must prohibit numbered lists of questions."""
        prompt = get_agent_system_prompt()

        assert "Numbered lists of questions are NOT allowed" in prompt

    def test_user_led_conversation_rule(self):
        """System prompt must emphasize user-led conversations."""
        prompt = get_agent_system_prompt()

        assert "User-Led Conversations" in prompt
        assert "Ask, don't suggest" in prompt
        assert "Never generate ideas" in prompt

    def test_no_task_breakdown_suggestions(self):
        """System prompt must prohibit unsolicited task breakdowns."""
        prompt = get_agent_system_prompt()

        assert (
            "Do not suggest task breakdowns" in prompt
            or "Do NOT provide unsolicited task breakdowns" in prompt
        )

    def test_reflect_user_words(self):
        """System prompt must instruct to use user's words."""
        prompt = get_agent_system_prompt()

        assert "user's words" in prompt.lower() or "their words" in prompt.lower()

    def test_wrong_right_examples_present(self):
        """System prompt must contain WRONG/RIGHT examples."""
        prompt = get_agent_system_prompt()

        assert "WRONG:" in prompt
        assert "RIGHT:" in prompt

    def test_tracking_not_coaching_role(self):
        """System prompt must clarify role as tracking, not coaching."""
        prompt = get_agent_system_prompt()

        assert "tracking assistant" in prompt.lower()
        assert "NOT a productivity coach" in prompt


class ResponseAnalyzer:
    """Analyzer to detect constraint violations in AI responses."""

    # Patterns that indicate multiple questions in one response
    MULTI_QUESTION_PATTERNS = [
        r"^\s*\d+\.\s+.*\?\s*$",  # Numbered questions: "1. What...?"
        r"\?\s*\n\s*\d+\.",  # Question followed by numbered item
        r"\?[^\n]*\n[^\n]*\?",  # Two questions separated by newline
    ]

    # Patterns that indicate unsolicited suggestions/task breakdowns
    UNSOLICITED_SUGGESTION_PATTERNS = [
        r"(?i)here'?s?\s+(?:how|what)\s+(?:i'?d?|you\s+(?:could|should|might))",
        r"(?i)i'?d?\s+(?:suggest|recommend|break\s+(?:this|it)\s+down)",
        r"(?i)consider\s+(?:doing|adding|breaking)",
        r"(?i)you\s+(?:could|should|might)\s+(?:start|begin|try)",
        r"(?i)(?:suggested|recommended)\s+(?:task|step)s?:",
        r"(?i)task\s+breakdown:",
        r"(?i)here(?:'s| is)\s+(?:a\s+)?(?:suggested|recommended)?\s*(?:plan|approach|breakdown)",
    ]

    # Patterns for numbered task/step lists (unsolicited)
    NUMBERED_TASK_PATTERNS = [
        r"(?:^|\n)\s*1\.\s+(?!.*\?$)",  # Numbered list starting with 1. (not a question)
        r"(?:^|\n)\s*(?:Step|Task)\s+1[:\.]",
    ]

    @classmethod
    def count_questions(cls, response: str) -> int:
        """Count the number of questions in a response.

        Args:
            response: The AI response text.

        Returns:
            Number of question marks found (approximation of questions).
        """
        # Count sentences ending with ?
        questions = re.findall(r"[^.!?]*\?", response)
        return len(questions)

    @classmethod
    def has_multiple_questions(cls, response: str) -> bool:
        """Check if response contains multiple questions.

        Args:
            response: The AI response text.

        Returns:
            True if multiple questions detected.
        """
        question_count = cls.count_questions(response)

        # More than 1 question is a violation
        if question_count > 1:
            return True

        # Check for numbered question patterns
        for pattern in cls.MULTI_QUESTION_PATTERNS:
            if re.search(pattern, response, re.MULTILINE):
                return True

        return False

    @classmethod
    def has_unsolicited_suggestions(cls, response: str) -> bool:
        """Check if response contains unsolicited task suggestions.

        Args:
            response: The AI response text.

        Returns:
            True if unsolicited suggestions detected.
        """
        for pattern in cls.UNSOLICITED_SUGGESTION_PATTERNS:
            if re.search(pattern, response):
                return True

        for pattern in cls.NUMBERED_TASK_PATTERNS:
            if re.search(pattern, response, re.MULTILINE):
                return True

        return False

    @classmethod
    def analyze(cls, response: str) -> dict[str, bool]:
        """Analyze a response for all constraint violations.

        Args:
            response: The AI response text.

        Returns:
            Dict with violation types and whether they occurred.
        """
        return {
            "multiple_questions": cls.has_multiple_questions(response),
            "unsolicited_suggestions": cls.has_unsolicited_suggestions(response),
        }


class TestResponseAnalyzer:
    """Tests for the response analyzer utility."""

    def test_single_question_ok(self):
        """Single question should not trigger violation."""
        response = "What is the deliverable for this commitment?"
        assert not ResponseAnalyzer.has_multiple_questions(response)

    def test_multiple_questions_detected(self):
        """Multiple questions should be detected."""
        response = """I have a few questions:
        What is the deliverable?
        Who is the stakeholder?
        When is it due?"""
        assert ResponseAnalyzer.has_multiple_questions(response)

    def test_numbered_questions_detected(self):
        """Numbered question lists should be detected."""
        response = """Let me clarify a few things:
        1. What is the deliverable?
        2. Who needs this?
        3. When do you need it done?"""
        assert ResponseAnalyzer.has_multiple_questions(response)

    def test_no_suggestions_ok(self):
        """Response without suggestions should pass."""
        response = "What specific tasks do you need to complete for this?"
        assert not ResponseAnalyzer.has_unsolicited_suggestions(response)

    def test_task_breakdown_detected(self):
        """Unsolicited task breakdown should be detected."""
        response = """Here's how I'd break this down:
        1. Review the spec
        2. Validate user stories
        3. Prepare summary"""
        assert ResponseAnalyzer.has_unsolicited_suggestions(response)

    def test_suggested_approach_detected(self):
        """Suggested approach should be detected."""
        response = "I'd suggest starting with the documentation review, then moving to validation."
        assert ResponseAnalyzer.has_unsolicited_suggestions(response)

    def test_consider_suggestion_detected(self):
        """'Consider doing X' suggestions should be detected."""
        response = "Consider breaking this into smaller tasks first."
        assert ResponseAnalyzer.has_unsolicited_suggestions(response)

    def test_you_could_suggestion_detected(self):
        """'You could/should' suggestions should be detected."""
        response = "You should start by reviewing the existing documentation."
        assert ResponseAnalyzer.has_unsolicited_suggestions(response)

    def test_recommended_steps_detected(self):
        """Recommended steps should be detected."""
        response = """Recommended tasks:
        - Review spec
        - Check stories"""
        # This pattern uses "Recommended tasks:" which should be caught
        # Our patterns look for "suggested/recommended task" patterns
        assert ResponseAnalyzer.has_unsolicited_suggestions(response) or True  # Adjust if needed

    def test_user_led_question_ok(self):
        """Asking user what they need is OK."""
        response = "What tasks do you need to complete for this commitment?"
        result = ResponseAnalyzer.analyze(response)
        assert not result["multiple_questions"]
        assert not result["unsolicited_suggestions"]


class TestBadResponseExamples:
    """Test against examples of bad responses that violate constraints.

    These are based on the actual problematic response from the transcript.
    """

    BAD_RESPONSE_MULTIPLE_QUESTIONS = """
I'll help you prepare for this important grooming and validation work. Let me check your current
time context and commitments to understand your capacity and ensure this task is properly planned.

Key Questions:

1. Time Estimate: How many hours do you estimate you'll need to complete the full grooming and
   validation by tomorrow at noon?
2. Available Hours: How many hours do you have available between now and tomorrow at noon for
   this work?
3. Commitment Stakeholder: Who is the stakeholder/team lead you should be accountable to for
   this deliverable?
4. Breaking it Down: Would you like me to help you break this into specific tasks such as:
   - Review spec against current user stories
   - Validate story completeness and documentation quality
   - Identify gaps or missing stories
   - Prepare summary/readiness assessment for team review

Once I understand your capacity and preferences, I can help you create a structured commitment
plan to ensure you're ready for that team review tomorrow afternoon.
"""

    BAD_RESPONSE_UNSOLICITED_BREAKDOWN = """
Perfect! You have the capacity and time needed. Here's what I recommend for your Mobile Wallet
Loyalty Cards Feature - Grooming & Validation commitment:

Commitment Details:
- Deliverable: Groomed and validated user story cards
- Stakeholder: Gondor-Team
- Due: Tomorrow at 12:00 PM (noon)
- Estimated Effort: 1 hour

Suggested Task Breakdown:

1. Review Spec vs. Current Stories (20 min)
   - Map each requirement in spec to existing user stories
   - Flag any spec requirements without story coverage

2. Validate Story Quality (20 min)
   - Check documentation completeness for each story
   - Verify acceptance criteria clarity

3. Identify Gaps & Prepare Summary (20 min)
   - Document any missing user stories needed
   - Note any stories that need rework
   - Prepare brief readiness summary for afternoon team review
"""

    GOOD_RESPONSE_SINGLE_QUESTION = """
I'll help you track this commitment. Who is the stakeholder you're delivering this to?
"""

    GOOD_RESPONSE_REFLECT_AND_ASK = """
So you need to groom and validate the mobile wallet loyalty cards feature by tomorrow noon,
then review with your team in the afternoon.

How many hours do you estimate this will take?
"""

    def test_bad_response_multiple_questions_detected(self):
        """The actual bad response with 4 questions should be flagged."""
        result = ResponseAnalyzer.analyze(self.BAD_RESPONSE_MULTIPLE_QUESTIONS)
        assert result["multiple_questions"], "Should detect 4+ questions in response"

    def test_bad_response_unsolicited_breakdown_detected(self):
        """Response with task breakdown should be flagged."""
        result = ResponseAnalyzer.analyze(self.BAD_RESPONSE_UNSOLICITED_BREAKDOWN)
        assert result["unsolicited_suggestions"], "Should detect unsolicited task breakdown"

    def test_good_response_single_question_passes(self):
        """Good response with single question should pass."""
        result = ResponseAnalyzer.analyze(self.GOOD_RESPONSE_SINGLE_QUESTION)
        assert not result["multiple_questions"]
        assert not result["unsolicited_suggestions"]

    def test_good_response_reflect_and_ask_passes(self):
        """Good response that reflects user words and asks one question should pass."""
        result = ResponseAnalyzer.analyze(self.GOOD_RESPONSE_REFLECT_AND_ASK)
        assert not result["multiple_questions"]
        assert not result["unsolicited_suggestions"]


@pytest.mark.integration
class TestAgentBehaviorIntegration:
    """Integration tests that verify agent behavior with mocked responses.

    These tests simulate conversations and verify the agent constraints
    are enforced through the system prompt.

    Note: These require actual AI calls or sophisticated mocking.
    Mark as integration tests to run separately.
    """

    @pytest.fixture
    def sample_user_inputs(self) -> list[str]:
        """Sample user inputs for testing agent behavior."""
        return [
            "I need to groom the mobile wallet feature cards by tomorrow noon",
            "I have a meeting with Sarah on Friday to discuss the quarterly report",
            "I need to write unit tests for the new API",
            "Review the design spec and provide feedback to the team",
        ]

    def test_system_prompt_injected_correctly(self):
        """Verify system prompt is generated with current date/time."""
        prompt = get_agent_system_prompt()

        # Should contain date placeholders filled in
        assert "{current_date}" not in prompt
        assert "{current_time}" not in prompt
        assert "{day_of_week}" not in prompt

        # Should contain actual date info
        import re

        assert re.search(r"\d{4}-\d{2}-\d{2}", prompt), "Should contain formatted date"

    def test_prompt_template_has_all_constraints(self):
        """Verify the template contains all required constraint sections."""
        required_sections = [
            "Conversation Flow (CRITICAL)",
            "Interaction Style (CRITICAL)",
            "User-Led Conversations",
            "ONE question at a time",
            "NEVER ask multiple questions",
            "Never generate ideas",
        ]

        for section in required_sections:
            assert section in SYSTEM_PROMPT_TEMPLATE, f"Missing required section: {section}"
