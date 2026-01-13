# Tasks: Add Commitment Coaching Guidance

## 1. System Prompt Update

- [x] 1.1 Add "Commitment-First Coaching" subsection to existing "Coaching Behaviors" section in `src/jdo/ai/agent.py`

**Implementation guidance** (per architectural research):
- Add ~10-15 lines, not ~50
- Place within existing "Coaching Behaviors" section (lines 83-104)
- Focus on examples over explanation - LLMs generalize well from examples

Suggested prompt addition:
```
### Commitment-First Coaching
When user describes work without a stakeholder or deliverable (e.g., "write tests", "gather data"):
1. Ask ONE clarifying question: "What will you deliver, and who needs it?"
2. If they provide context, propose a commitment with the work as a task
3. If they decline, acknowledge and offer to help link to a commitment later (don't block)
```

## 2. Testing

- [x] 2.1 Add unit test verifying system prompt contains "Commitment-First Coaching" section
  - Verify: Test passes with `uv run pytest tests/unit/ai/test_agent.py -v -k coaching`
- [ ] 2.2 Manual test: verify AI asks clarifying question for task-like input
  - Verify: Enter "I need to write unit tests" and confirm AI asks about deliverable/stakeholder
- [ ] 2.3 Manual test: verify AI proceeds directly when full context provided
  - Verify: Enter "I need to send the report to Sarah by Friday" and confirm AI creates commitment
- [ ] 2.4 Manual test: verify AI handles partial context gracefully
  - Verify: When asked coaching question, respond "it's for Sarah" and confirm AI asks ONE follow-up

## 3. Validation

- [x] 3.1 Run `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/`
- [x] 3.2 Run `uvx pyrefly check src/`
- [x] 3.3 Run `uv run pytest -n auto`

## Dependencies

- Task 1.1 is the only implementation task
- Task 2.1 depends on 1.1 completion
- Tasks 2.2-2.4 are manual verification (require AI provider)
- Task 3.x depends on all implementation being complete

## Research Notes

Per architectural validation (2026-01-13):
- "Task vs Commitment Education" is emergent behavior - LLMs naturally explain when asked
- "Contextual Commitment Suggestions" is handled by existing message history
- No additional state management needed
- Single requirement replaces original 3 requirements
