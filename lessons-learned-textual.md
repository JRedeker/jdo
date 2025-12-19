# Lessons Learned: Textual TUI Development

This document captures bugs, workarounds, and hard-won knowledge from building the JDO TUI with Textual. These lessons complement the patterns documented in `docs/textual-patterns.md`.

---

## Table of Contents

1. [Textual Framework Bugs](#textual-framework-bugs)
2. [Testing Gotchas](#testing-gotchas)
3. [Type Checking Issues](#type-checking-issues)
4. [Screen and Navigation Issues](#screen-and-navigation-issues)
5. [Widget Development Issues](#widget-development-issues)
6. [Worker and Async Issues](#worker-and-async-issues)
7. [Test Pattern Notes](#test-pattern-notes)
8. [Quick Reference: Common Fixes](#quick-reference-common-fixes)
9. [Additional Patterns from Official Docs](#additional-patterns-from-official-docs)

---

## Textual Framework Bugs

### Selection Coordinates Bug (Textual 6.9.0)

**Problem**: Clicking on a widget or attempting text selection causes `IndexError: list index out of range` crash.

**Root Cause**: Textual's `Selection` object passes screen-relative coordinates (e.g., `y=6`) to `widget.get_selection()`, but the widget's text content may only have 2-3 lines. When `selection.extract(text)` tries to access `lines[6]`, it crashes.

**Symptoms**:
```
IndexError: list index out of range
  File "textual/selection.py", line 66, in extract
    return lines[start_line][start_offset:end_offset]
```

**Workaround**: Override `get_selection()` in affected widgets to catch `IndexError`:

```python
from textual.content import Content
from textual.selection import Selection
from rich.text import Text

class ChatMessage(Static):
    def get_selection(self, selection: Selection) -> tuple[str, str] | None:
        """Handle out-of-range selection coordinates gracefully."""
        visual = self._render()
        if isinstance(visual, (Text, Content)):
            text = str(visual)
        else:
            return None

        try:
            extracted = selection.extract(text)
        except IndexError:
            # Selection coordinates are out of range for this widget's text
            return None
        else:
            return extracted, "\n"
```

**Note**: The `get_selection()` method and `Selection` class are not extensively documented in official Textual docs, suggesting this is internal/advanced API. The workaround is defensive programming against coordinate mismatch.

**Status**: Workaround applied in `src/jdo/widgets/chat_message.py`. Should be reported upstream to Textual.

**Affected Version**: Textual 6.9.0

---

## Testing Gotchas

### Screen Composition vs Screen Pushing

**Problem**: Tests using `yield Screen()` in `compose()` caused focus tracking issues where `prompt.has_focus` was `True` but `pilot.app.focused` pointed to wrong widget.

**Wrong Approach**:
```python
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield ChatScreen()  # Don't do this!
```

**Correct Approach**:
```python
class TestApp(App):
    def on_mount(self) -> None:
        self.push_screen(ChatScreen())  # Note: no 'await' needed

# In test:
async with app.run_test() as pilot:
    await pilot.pause()  # Wait for screen to mount
    screen = pilot.app.screen  # Query from screen, not app
```

**Key Points**:
- Use `push_screen()` in `on_mount()`, not `yield` in `compose()`
- `push_screen()` returns immediately (no await needed for basic usage)
- Add `await pilot.pause()` before querying widgets after screen push
- Query widgets from `pilot.app.screen` not `pilot.app`

**Alternative - Using SCREENS dict** (from official docs):
```python
class MyApp(App):
    SCREENS = {"chat": ChatScreen}
    
    def on_mount(self) -> None:
        self.push_screen("chat")
```

**Reference**: [Textual Screens Guide](https://textual.textualize.io/guide/screens/)

**Commit**: `74bc66b` - Fix ChatScreen integration tests to properly push screens

---

### Pilot Testing Timing

**Problem**: Widget queries fail because screen hasn't mounted yet.

**Solution**: Always `await pilot.pause()` after actions that change screens or mount widgets:

```python
async with app.run_test() as pilot:
    await pilot.press("g")  # Trigger navigation
    await pilot.pause()      # Wait for screen transition
    
    # Now safe to query
    assert isinstance(pilot.app.screen, ChatScreen)
```

**With optional delay** (for longer async operations):
```python
await pilot.pause(delay=0.1)  # Wait 0.1 seconds, then process messages
```

**Reference**: [Textual Testing Guide](https://textual.textualize.io/guide/testing/)

---

## Type Checking Issues

### Pyrefly False Positives

**Problem**: Pyrefly reports type errors on valid Textual/Rich code.

**Known False Positives** (safe to ignore):
- `Rich Text.append()` with certain argument types
- `Textual reactive attributes`
- SQLModel/SQLAlchemy column comparisons (`.in_()`, `.order_by()`)

**Solution**: Document in `AGENTS.md` under "Known Tool Limitations" and verify at runtime.

**Commit**: `359a77a` - Fix pyrefly type warnings

---

### ClassVar for Mutable Class Attributes

**Problem**: Type checkers may report errors on mutable class attributes like `BINDINGS` without proper annotation.

**Note**: The official Textual documentation does NOT require `ClassVar` - this is a **type checker accommodation**:
```python
# Official Textual docs style (works fine at runtime):
class MyWidget(Widget):
    BINDINGS = [Binding("enter", "submit", "Submit")]
```

**For strict type checkers** (like pyrefly), add `ClassVar`:
```python
from typing import ClassVar

class MyWidget(Widget):
    BINDINGS: ClassVar[list[Binding]] = [
        Binding("enter", "submit", "Submit"),
    ]
```

**Reference**: [Textual Bindings Guide](https://textual.textualize.io/guide/input/#bindings)

---

### Return Type for compose()

**Problem**: `compose()` methods need explicit return type annotation for type checkers.

**Official Pattern** (from Textual docs):
```python
from textual.app import ComposeResult

def compose(self) -> ComposeResult:
    yield SomeChild()
```

**Alternative** (also valid, but less idiomatic):
```python
from collections.abc import Iterator
from textual.widget import Widget

def compose(self) -> Iterator[Widget]:
    yield SomeChild()
```

**Note**: `ComposeResult` is the canonical type alias used throughout official Textual documentation. It's defined as `Iterable[Widget]` internally.

**Reference**: [Textual App Guide - compose()](https://textual.textualize.io/guide/app/#compose)

---

## Screen and Navigation Issues

### Missing Message Handlers

**Problem**: HomeScreen had 10 keyboard shortcuts but only 4 message handlers in JdoApp, causing 6 shortcuts to do nothing.

**Symptoms**: Pressing shortcut keys (g, c, v, m, o, h, i) had no effect.

**Root Cause**: Screens post messages, but App must handle them. Each `post_message()` needs a corresponding `on_<screen>_<message>()` handler.

**Solution**: Audit all screen messages and ensure App has handlers for each:

```python
# Screen defines message and posts it
class HomeScreen(Screen):
    class ShowGoals(Message):
        """Request to show goals list."""
    
    def action_show_goals(self) -> None:
        self.post_message(self.ShowGoals())

# App MUST have handler
class JdoApp(App):
    def on_home_screen_show_goals(self, _message: HomeScreen.ShowGoals) -> None:
        # Handle the navigation
        self.push_screen(ChatScreen(...))
```

**Handler naming convention**: `on_<widget_class>_<message_class>` in snake_case.

**Tip**: You can programmatically check the expected handler name:
```python
>>> HomeScreen.ShowGoals.handler_name
'on_home_screen_show_goals'
```

**Alternative**: Use the `@on` decorator for targeted handling:
```python
from textual import on

@on(HomeScreen.ShowGoals)
def handle_show_goals(self, message: HomeScreen.ShowGoals) -> None:
    self.push_screen(ChatScreen(...))
```

**Checklist**: For every `post_message()` call, verify the parent has a handler.

**Reference**: [Textual Events Guide - Message Handlers](https://textual.textualize.io/guide/events/)

**Commit**: `a06c12f` - Fix navigation shortcuts and reduce code complexity

---

### Screen Initialization Complexity

**Problem**: ChatScreen had 9 `__init__` parameters, making it hard to use and test.

**Solution**: Extract a config dataclass to group related parameters:

```python
@dataclass
class ChatScreenConfig:
    """Configuration for ChatScreen initialization."""
    draft_id: UUID | None = None
    triage_mode: bool = False
    initial_mode: str | None = None
    initial_entity_type: str | None = None
    initial_data: list[dict[str, Any]] | dict[str, Any] | None = None

# Usage becomes cleaner
self.push_screen(
    ChatScreen(
        ChatScreenConfig(
            initial_mode="list",
            initial_entity_type="goal",
            initial_data=goal_items,
        )
    )
)
```

**Benefits**:
- Reduces parameter count (9 → 4)
- Self-documenting at call sites
- Easier to extend without breaking API

**Commit**: `a06c12f` - Extract ChatScreenConfig dataclass

---

## Widget Development Issues

### Content Import Path

**Problem**: `textual._content.Content` is a private module that may change.

**Wrong**:
```python
from textual._content import Content  # Private, may break
```

**Correct**:
```python
from textual.content import Content  # Public API
```

**Usage example** (from official docs):
```python
from textual.content import Content

# Create literal content
content = Content("Hello, World!")

# Create content with markup
content = Content.from_markup("Hello, [bold]World[/bold]!")

# Stylize content (returns new instance - Content is immutable)
content = content.stylize(7, 12, "bold")
```

**Reference**: [Textual Content Guide](https://textual.textualize.io/guide/content/)

---

### Widget State Initialization

**Problem**: Accessing attributes before `__init__` completes causes `AttributeError`.

**Solution**: Use `getattr()` with defaults in properties:

```python
@property
def is_thinking(self) -> bool:
    """Check if the message is in thinking state."""
    return getattr(self, "_is_thinking", False)

@property
def recoverable(self) -> bool:
    """Check if this is a recoverable error message."""
    return getattr(self, "_recoverable", True)
```

---

## Worker and Async Issues

### NoActiveWorker Exception

**Problem**: `push_screen_wait()` in `on_mount()` raises `RuntimeError: There is no currently active worker`.

**Why**: `push_screen_wait()` is designed to be called from within a worker context. Calling it directly from `on_mount()` fails because there's no active worker.

**Wrong**:
```python
async def on_mount(self):
    result = await self.push_screen_wait(SomeScreen())
```

**Correct Option 1** - Using `@work` decorator (preferred):
```python
from textual.worker import work

def on_mount(self):
    self._async_flow()

@work
async def _async_flow(self):
    result = await self.push_screen_wait(SomeScreen())
```

**Correct Option 2** - Using `run_worker()`:
```python
def on_mount(self):
    self.run_worker(self._async_flow(), exclusive=True)

async def _async_flow(self):
    result = await self.push_screen_wait(SomeScreen())
```

**Rule**: Any blocking screen operation (`push_screen_wait`) needs worker context.

**Reference**: [Textual Screens - Waiting for screens](https://textual.textualize.io/guide/screens/#waiting-for-screens)

---

### Worker Cancellation During Streaming

**Problem**: AI streaming continues after user navigates away.

**Solution**: Check worker cancellation status in loops using `get_current_worker()`:

```python
from textual.worker import get_current_worker

async def _do_ai_streaming(self, prompt: str) -> None:
    worker = get_current_worker()
    
    async for chunk in stream_response(...):
        if worker.is_cancelled:
            break
        await self.chat_container.append_to_last(chunk)
```

**For thread workers**, the pattern is similar:
```python
from textual.worker import get_current_worker, work

@work(thread=True)
def blocking_operation(self) -> None:
    worker = get_current_worker()
    for item in long_running_iterator():
        if worker.is_cancelled:
            return
        # process item
```

**Note**: `is_cancelled` is a property that returns `True` if `cancel()` was called. Cancelled work may still be running until it checks this property.

**Reference**: [Textual Workers - Thread workers](https://textual.textualize.io/guide/workers/#thread-workers)

---

## Test Pattern Notes

### Yielding Screens in Test compose() Methods

**Note**: Many existing test files yield screens directly in `compose()` instead of pushing them in `on_mount()`. This can cause focus tracking issues.

**For NEW tests**, use the helper function in `tests/tui/conftest.py`:

```python
from tests.tui.conftest import create_test_app_for_screen
from jdo.screens.chat import ChatScreen

async def test_something() -> None:
    app = create_test_app_for_screen(ChatScreen())
    async with app.run_test() as pilot:
        await pilot.pause()  # IMPORTANT: Wait for screen to mount
        screen = pilot.app.screen  # Query from screen, not app
        # ... test assertions
```

**Legacy pattern** (avoid in new tests):

```python
# Old pattern - works but can cause focus tracking issues
class TestApp(App):
    def compose(self) -> ComposeResult:
        yield ChatScreen()  # Avoid this in new tests
```

**Status**: Migration complete. All TUI test files now use the `create_test_app_for_screen()` helper or the proper `push_screen()` pattern. Migrated files include test_settings_screen.py, test_home_screen.py, test_architecture.py, test_snapshots.py, and test_chat_screen.py (44 tests). New tests MUST use `create_test_app_for_screen()`.

### Best Practices for TUI Tests

1. **Always `await pilot.pause()`** after screen pushes or major widget changes
2. **Query from `pilot.app.screen`** instead of `pilot.app` after navigation
3. **Use double pause** for async operations: `await pilot.pause(); await pilot.pause()`

---

## Quick Reference: Common Fixes

| Issue | Fix |
|-------|-----|
| `NoActiveWorker` | Wrap in `run_worker()` |
| Missing navigation | Add message handler in App |
| Focus not working | Query from `pilot.app.screen` |
| Type error on `BINDINGS` | Add `ClassVar` annotation |
| Selection crash | Override `get_selection()` with try/except |
| Test timing issues | Add `await pilot.pause()` |
| Screen init complexity | Extract config dataclass |
| Dead message classes | Remove if never posted |

---

## Additional Patterns from Official Docs

### Thread-Safe UI Updates

**Problem**: Most Textual functions are NOT thread-safe when called from thread workers.

**Solution**: Use `call_from_thread()` for UI updates from thread workers:

```python
from textual.worker import work, get_current_worker

@work(thread=True)
def blocking_operation(self) -> None:
    worker = get_current_worker()
    # Do blocking work...
    result = some_blocking_api()
    
    # Update UI safely
    self.call_from_thread(self.update_display, result)

def update_display(self, result: str) -> None:
    """This runs in the main Textual thread."""
    self.query_one("#status").update(result)
```

**Exception**: `post_message()` IS thread-safe and can be called directly from thread workers.

**Reference**: [Textual Workers - Thread workers](https://textual.textualize.io/guide/workers/#thread-workers)

---

### Reactive Attributes with Mutable Types

**Problem**: Textual cannot detect mutations within mutable objects (lists, dicts).

**Solution**: Call `mutate_reactive()` after modifying mutable reactive attributes:

```python
from textual.reactive import reactive

class MyWidget(Widget):
    items = reactive([])
    
    def add_item(self, item: str) -> None:
        self.items.append(item)  # Mutation not detected automatically
        self.mutate_reactive(MyWidget.items)  # Trigger watchers manually
```

**Reference**: [Textual Reactivity - Mutable reactives](https://textual.textualize.io/guide/reactivity/)

---

### Using the @on Decorator for Targeted Event Handling

**Problem**: Single message handler becomes complex with many widgets of same type.

**Solution**: Use `@on` decorator with CSS selectors:

```python
from textual import on
from textual.widgets import Button

@on(Button.Pressed, "#save-btn")
def handle_save(self) -> None:
    """Only handles save button."""
    self.save()

@on(Button.Pressed, "#cancel-btn")
def handle_cancel(self) -> None:
    """Only handles cancel button."""
    self.cancel()

@on(Button.Pressed, ".danger")
def handle_danger_buttons(self) -> None:
    """Handles any button with 'danger' class."""
    self.confirm_action()
```

**Reference**: [Textual Events - on decorator](https://textual.textualize.io/guide/events/)

---

### Worker Lifetime Management

**Problem**: Workers may continue running after their parent widget is removed.

**Solution**: Workers are automatically tied to their DOM node lifecycle:
- Removing a widget cancels its workers
- Popping a screen cancels its workers
- Exiting the app cancels all workers

**Explicit cancellation**:
```python
worker = self.run_worker(long_task())
# Later...
worker.cancel()  # Raises CancelledError in the coroutine
```

**Reference**: [Textual Workers - Worker lifetime](https://textual.textualize.io/guide/workers/#worker-lifetime)

---

## Related Documentation

- `docs/textual-patterns.md` - Comprehensive patterns guide
- `AGENTS.md` - Project coding standards including Textual conventions
- [Textual Documentation](https://textual.textualize.io/)
- [Textual Guide - Testing](https://textual.textualize.io/guide/testing/)
- [Textual Guide - Workers](https://textual.textualize.io/guide/workers/)
- [Textual Guide - Screens](https://textual.textualize.io/guide/screens/)
- [Textual Guide - Events](https://textual.textualize.io/guide/events/)
- [Textual Guide - Reactivity](https://textual.textualize.io/guide/reactivity/)

---

**Document Version**: 1.1
**Last Updated**: 2025-12-18
**Textual Version**: 6.9.0
**Verified Against**: Official Textual documentation (Context7)
