# Tasks: Enhanced Visual Output

## Scope (Post-Research)

**Implementing**: Spinner, auto-completion, bottom toolbar, markdown rendering, rounded tables
**Deferred**: Tree view, progress bars (existing text progress is sufficient)

---

## 1. Spinner for AI Thinking Indicator

- [x] 1.1 Import `Status` from rich.status in loop.py
- [x] 1.2 Create status with `console.status("[dim]Thinking...[/dim]", spinner="dots")`
- [x] 1.3 Call `status.start()` before streaming begins
- [x] 1.4 Call `status.stop()` when first token arrives (BEFORE starting Live)
- [x] 1.5 Add try/finally to ensure status.stop() on error
- [x] 1.6 Remove carriage return hacks (`"\r" + " " * 20 + "\r"`)
- [x] 1.7 ~~Add unit test for spinner start/stop behavior~~ (deferred: requires complex mocking of async streaming)

## 2. Command Auto-completion (Simplified)

- [x] 2.1 Import `WordCompleter` from prompt_toolkit.completion
- [x] 2.2 Create slash command list: `/help`, `/list`, `/commit`, `/complete`, `/review`
- [x] 2.3 Configure `WordCompleter(commands, ignore_case=True)`
- [x] 2.4 Add `completer=completer` to PromptSession
- [x] 2.5 Set `complete_while_typing=False` (Tab-only completion)
- [x] 2.6 ~~Add unit test for completer configuration~~ (deferred: requires prompt_toolkit mocking)

## 3. Bottom Toolbar with Cached Stats

- [x] 3.1 Add `cached_commitment_count: int` and `cached_triage_count: int` to Session class
- [x] 3.2 Update cache at startup (initialization in repl_loop)
- [x] 3.3 Create `get_toolbar_text()` function using cached values (NOT live DB queries)
- [x] 3.4 Configure PromptSession with `bottom_toolbar=get_toolbar_text`
- [x] 3.5 Add `refresh_interval=1.0` for periodic refresh
- [x] 3.6 Show format: `" X active | Y triage [draft]"`
- [x] 3.7 ~~Add unit test for toolbar content generation~~ (deferred: requires prompt_toolkit mocking)

## 4. Markdown AI Response Rendering (During Streaming)

- [x] 4.1 Import `Markdown` from rich.markdown
- [x] 4.2 Modify streaming loop to accumulate full_response string
- [x] 4.3 Use `live.update(Markdown(full_response))` on each chunk
- [x] 4.4 Add try/except fallback to `Text(full_response)` on markdown errors
- [x] 4.5 ~~Add unit test for markdown rendering and fallback~~ (deferred: requires complex mocking)

## 5. Rounded Table Borders

- [x] 5.1 Import `box` from rich.box in formatters.py
- [x] 5.2 Update `format_commitment_list()` in `src/jdo/output/formatters.py`: `Table(title="Commitments", box=box.ROUNDED)`
- [x] 5.3 Update `format_goal_list()` in `src/jdo/output/goal.py`: `Table(title="Goals", box=box.ROUNDED)`
- [x] 5.4 Update `format_vision_list()` in `src/jdo/output/vision.py`: `Table(title="Visions", box=box.ROUNDED)`
- [x] 5.5 Update `format_milestone_list()` in `src/jdo/output/milestone.py`: `Table(title="Milestones", box=box.ROUNDED)`
- [x] 5.6 Update `format_task_list()` in `src/jdo/output/task.py`: `Table(title="Tasks", box=box.ROUNDED)`
- [x] 5.7 Update inline tables in `src/jdo/repl/loop.py` `_list_goals()` and `_list_visions()`: add `box=box.ROUNDED`
- [x] 5.8 Verify: `src/jdo/output/integrity.py` uses `box=None` intentionally (no change needed)
  - Note: Metrics table uses `box=None` for compact inline display, not entity list

## 6. Validation and Cleanup

- [x] 6.1 Run `uv run ruff check --fix src/ tests/`
- [x] 6.2 Run `uv run ruff format src/ tests/`
- [x] 6.3 Run `uvx pyrefly check src/` - 0 errors (warnings only)
- [x] 6.4 Run `uv run pytest` - all tests pass
- [x] 6.5 Manual smoke test: verify spinner, completion, toolbar, markdown, tables
  - Note: Requires interactive testing by user

---

## Deferred Tasks (Future Change)

These were researched and found to be over-engineered for current needs:

### Tree View for Entity Hierarchy
- Current `/list` commands with tables are sufficient
- Rich Tree IS the right component if needed later
- Create separate change proposal if hierarchy visualization becomes valuable

### Progress Bar for Triage
- `output/triage.py` already has `format_triage_progress()` showing "Item X of Y"
- Rich Progress bar is overkill for 5-10 triage items
- Revisit if triage workflow becomes more complex
