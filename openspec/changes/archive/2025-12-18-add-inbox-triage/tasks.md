# Tasks: Add Inbox Capture and Triage System

## 1. Data Model Foundation

- [x] 1.1 Add `UNKNOWN = "unknown"` to `EntityType` enum in `src/jdo/models/draft.py`
- [x] 1.2 Add `get_triage_items(session) -> list[Draft]` query helper to `src/jdo/db/session.py`
- [x] 1.3 Add `get_triage_count(session) -> int` helper for home screen badge
- [x] 1.4 Write unit tests for new EntityType value and query helpers

## 2. CLI Capture Command

- [x] 2.1 Add Click dependency to `pyproject.toml` for CLI subcommand support
- [x] 2.2 Create `src/jdo/cli.py` with `capture(text: str)` command
- [x] 2.3 Update `pyproject.toml` entry point: `jdo = "jdo.cli:main"` (wraps TUI + subcommands)
- [x] 2.4 Implement `capture` command: create Draft with `entity_type=UNKNOWN`, `partial_data={"raw_text": text}`
- [x] 2.5 Write integration tests for CLI capture → database persistence

## 3. Home Screen Triage Indicator

- [x] 3.1 Add `_triage_count` reactive attribute to `HomeScreen`
- [x] 3.2 Add triage indicator widget: "N items need triage [t]" (hidden when N=0)
- [x] 3.3 Add `t` key binding to start triage mode
- [x] 3.4 Add `_check_triage_count()` method called on mount
- [x] 3.5 Write TUI tests for home screen indicator visibility

## 4. Triage Command Infrastructure

- [x] 4.1 Add `TRIAGE = "triage"` to `CommandType` enum in `src/jdo/commands/parser.py`
- [x] 4.2 Add `/triage` to command map in parser
- [x] 4.3 Create `TriageHandler` class in `src/jdo/commands/handlers.py`
- [x] 4.4 Register `TriageHandler` in handler registry
- [x] 4.5 Write unit tests for triage command parsing

## 5. AI Classification

- [x] 5.1 Create `src/jdo/ai/triage.py` with `TriageAnalysis` dataclass
- [x] 5.2 Implement `classify_triage_item(text, session) -> TriageAnalysis`
- [x] 5.3 Add specialized system prompt for classification with entity detection
- [x] 5.4 Implement confidence scoring and low-confidence clarifying questions
- [x] 5.5 Write unit tests with mocked AI responses

## 6. Triage Workflow

- [x] 6.1 Implement triage loop in `TriageHandler.execute()`
- [x] 6.2 Display AI analysis with options: Accept, Change type, Delete, Skip
- [x] 6.3 Handle "Accept": update draft entity_type, proceed to creation flow
- [x] 6.4 Handle "Change type": prompt for type, then proceed to creation
- [x] 6.5 Handle "Delete": remove draft from database
- [x] 6.6 Handle "Skip": move to next item (current stays at front)
- [x] 6.7 Handle workflow exit: save partial progress appropriately
- [x] 6.8 Write integration tests for full triage workflow

## 7. Chat Vague Input Detection

- [~] 7.1 Add `on_prompt_input_submitted()` handler to `ChatScreen` (deferred per design - not real-time)
- [~] 7.2 Create `src/jdo/ai/intent.py` with `detect_intent(text) -> IntentResult` (deferred)
- [~] 7.3 Implement low-confidence handling: create triage item, offer immediate triage (deferred)
- [~] 7.4 Handle user response to "Would you like to triage now?" (deferred)
- [~] 7.5 Write TUI tests for vague input → triage flow (deferred)

## 8. Integration & Polish

- [x] 8.1 Add `/triage` to help command output
- [x] 8.2 Update home screen footer to show `t` shortcut when triage items exist
- [x] 8.3 End-to-end test: CLI capture → home screen badge → triage → object creation
- [x] 8.4 Run full test suite and fix any regressions
- [x] 8.5 Run linting and type checking, resolve all errors
