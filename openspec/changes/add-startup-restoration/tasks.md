## 1. Vision Review Query

- [x] 1.1 ~~Add `get_visions_due_for_review(db_session) -> list[Vision]` to `src/jdo/db/session.py`~~ (Already exists at line 51-69)
- [x] 1.2 Verify existing unit test for vision review query (or add if missing)
  - Verify: `uv run pytest tests/ -k "visions_due" -v` passes

## 2. Session Snooze Tracking

- [x] 2.1 Add `self.snoozed_vision_ids: set[UUID] = set()` to `Session.__init__()` in `repl/session.py`
  - Verify: Write unit test that session tracks snoozed IDs correctly

## 3. Vision Review Notice on Startup

- [x] 3.1 Update `_show_startup_guidance()` signature to accept `session: Session` parameter
  - Update call site in `repl_loop()` to pass the session object
- [x] 3.2 Extend `_show_startup_guidance()` to check for visions due (using existing `get_visions_due_for_review`)
  - Filter out visions already in `session.snoozed_vision_ids`
  - Wrap query in try/except to handle database errors gracefully (log and continue)
- [x] 3.3 Display non-blocking notice with count and `/review` hint
  - Single vision: "Your vision '[title]' is due for review. Type /review to reflect on it."
  - Multiple: "You have N visions due for review. Type /review to start."
- [x] 3.4 Mark displayed visions as snoozed in session immediately after displaying notice
  - Add all returned vision IDs to `session.snoozed_vision_ids` after showing notice
  - This prevents notice from re-appearing if `_show_startup_guidance` is called again mid-session
- [x] 3.5 Write integration test for vision review notice
  - Verify: Test covers single vision, multiple visions, no visions due, and database error scenarios

## 4. Review Command (optional, if not already implemented)

- [x] 4.1 Add `/review` slash command to display first due vision and update review dates
- [x] 4.2 Write test for `/review` command

## 5. Validation

- [x] 5.1 Run `uv run ruff check src/ tests/ && uv run ruff format src/ tests/`
- [x] 5.2 Run `uvx pyrefly check src/`
- [x] 5.3 Run `uv run pytest` - all tests pass (1294 passed)
