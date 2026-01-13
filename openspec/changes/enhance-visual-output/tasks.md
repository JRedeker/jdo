# Tasks: Enhanced Visual Output

## Scope (Post-Research)

**Implementing**: Spinner, auto-completion, bottom toolbar, markdown rendering, rounded tables
**Deferred**: Tree view, progress bars (existing text progress is sufficient)

---

## 1. Spinner for AI Thinking Indicator

- [ ] 1.1 Import `Status` from rich.status in loop.py
- [ ] 1.2 Create status with `console.status("[dim]Thinking...[/dim]", spinner="dots")`
- [ ] 1.3 Call `status.start()` before streaming begins
- [ ] 1.4 Call `status.stop()` when first token arrives (BEFORE starting Live)
- [ ] 1.5 Add try/finally to ensure status.stop() on error
- [ ] 1.6 Remove carriage return hacks (`"\r" + " " * 20 + "\r"`)
- [ ] 1.7 Add unit test for spinner start/stop behavior

## 2. Command Auto-completion (Simplified)

- [ ] 2.1 Import `WordCompleter` from prompt_toolkit.completion
- [ ] 2.2 Create slash command list: `/help`, `/list`, `/commit`, `/complete`, `/review`
- [ ] 2.3 Configure `WordCompleter(commands, ignore_case=True)`
- [ ] 2.4 Add `completer=completer` to PromptSession
- [ ] 2.5 Set `complete_while_typing=False` (Tab-only completion)
- [ ] 2.6 Add unit test for completer configuration

## 3. Bottom Toolbar with Cached Stats

- [ ] 3.1 Add `cached_commitment_count: int` and `cached_triage_count: int` to Session class
- [ ] 3.2 Update cache after data-modifying operations (create, update, delete)
- [ ] 3.3 Create `_get_toolbar_text()` function using cached values (NOT live DB queries)
- [ ] 3.4 Configure PromptSession with `bottom_toolbar=_get_toolbar_text`
- [ ] 3.5 Add `refresh_interval=1.0` for periodic refresh
- [ ] 3.6 Show format: `" X active | Y triage [draft]"`
- [ ] 3.7 Add unit test for toolbar content generation

## 4. Markdown AI Response Rendering (During Streaming)

- [ ] 4.1 Import `Markdown` from rich.markdown
- [ ] 4.2 Modify streaming loop to accumulate full_response string
- [ ] 4.3 Use `live.update(Markdown(full_response))` on each chunk
- [ ] 4.4 Add try/except fallback to `Text(full_response)` on markdown errors
- [ ] 4.5 Add unit test for markdown rendering and fallback

## 5. Rounded Table Borders

- [ ] 5.1 Import `box` from rich.box in formatters.py
- [ ] 5.2 Update `format_commitment_list()`: `Table(title="Commitments", box=box.ROUNDED)`
- [ ] 5.3 Update goal table in loop.py `_list_goals()`
- [ ] 5.4 Update vision table in loop.py `_list_visions()`
- [ ] 5.5 Update any other Table instances in output modules

## 6. Validation and Cleanup

- [ ] 6.1 Run `uv run ruff check --fix src/ tests/`
- [ ] 6.2 Run `uv run ruff format src/ tests/`
- [ ] 6.3 Run `uvx pyrefly check src/`
- [ ] 6.4 Run `uv run pytest` - all tests pass
- [ ] 6.5 Manual smoke test: verify spinner, completion, toolbar, markdown, tables

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
