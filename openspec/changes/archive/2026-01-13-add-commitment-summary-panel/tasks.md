# Tasks: Add Commitment Summary Panel

## 1. Add Relative Date Formatter

- [x] 1.1 Add `format_relative_date(d: date, today: date | None = None) -> str` in `src/jdo/output/formatters.py`
  - Returns "Today" for same day
  - Returns "Tomorrow" for next day
  - Returns weekday abbreviation ("Fri", "Mon") for 2-6 days out
  - Returns "in X days" for 7+ days out
  - Returns ISO format for past dates (fallback)
- [x] 1.2 Add unit tests for `format_relative_date()`:
  - Test each relative date case
  - Test edge cases (end of week boundary, exactly 7 days)

## 2. Create Summary Panel Formatter

- [x] 2.1 Add `format_commitment_summary()` function in `src/jdo/output/formatters.py`
  - Input: summary data dict with `active_count`, `at_risk_count`, `next_due` info
  - Output: `Panel | None` (None if no active commitments)
- [x] 2.2 Implement panel styling per research findings:
  ```python
  from rich.panel import Panel
  from rich.text import Text
  from rich import box
  
  content = Text.assemble(
      ("📋 ", ""),
      (str(active_count), "bold"),
      (" active ", "dim"),
      # Add at-risk if > 0
      ("(", "dim"),
      (str(at_risk_count), "bold yellow"),
      (" ⚠️)", ""),
      ("  │  ", "dim"),
      ("Next: ", "dim"),
      (truncated_deliverable, "cyan"),
      (" → ", "dim"),
      (relative_date, "bold cyan"),
  )
  
  return Panel.fit(
      content,
      box=box.ROUNDED,
      border_style="dim",
      padding=(0, 1),
  )
  ```
- [x] 2.3 Handle edge cases:
  - No commitments: return None
  - No next due item: omit "Next:" section
  - Truncate deliverable to ~20 chars with "..."

## 3. Add Session Caching for Summary Data

- [x] 3.1 Extend `Session` class in `src/jdo/repl/session.py`:
  - Add `cached_at_risk_count: int = 0` field
  - Add `cached_next_due_deliverable: str | None = None` field
  - Add `cached_next_due_date: date | None = None` field
- [x] 3.2 Extend `update_cached_counts()` method to accept summary data
- [x] 3.3 Create helper function `_get_commitment_summary_data(db_session) -> dict`:
  - Query active commitments
  - Count by status (active, at_risk)
  - Find next due commitment (earliest due_date)
  - Return dict for caching

## 4. Integrate Summary Panel into REPL Loop

- [x] 4.1 Add `_show_commitment_summary()` function in `src/jdo/repl/loop.py`
  - Build summary data dict from session cache
  - Call `format_commitment_summary()` and print if not None
- [x] 4.2 Call `_show_commitment_summary()` in appropriate locations:
  - Before first prompt (in `_main_repl_loop`)
  - After each successful command/AI response (before next prompt)
- [x] 4.3 Update cached summary data when commitments change:
  - After `_confirm_draft()` creates commitment
  - After `_handle_complete()` completes commitment
  - Using new `_update_session_summary_cache()` helper

## 5. Testing

- [x] 5.1 Unit tests for `format_commitment_summary()`:
  - Empty summary returns None
  - Single commitment shows correctly with styling
  - Multiple commitments with at-risk items shows warning styling
  - Long deliverable truncation
  - No next due item (omits Next: section)
- [x] 5.2 Unit tests for `format_relative_date()`:
  - Today, Tomorrow, weekday names, "in X days", past date fallback

## 6. Validation

- [x] 6.1 Run lint/format: `uv run ruff check --fix src/ tests/ && uv run ruff format src/ tests/`
- [x] 6.2 Run tests: `uv run pytest` - 1570 tests passed
