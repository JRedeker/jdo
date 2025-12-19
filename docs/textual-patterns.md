# Textual Patterns and Best Practices

This document captures our Textual implementation patterns, common pitfalls, and best practices learned while building the JDO TUI.

## Table of Contents

1. [Worker Context Requirements](#worker-context-requirements)
2. [Async Lifecycle Methods](#async-lifecycle-methods)
3. [Message Handling](#message-handling)
4. [Screen Navigation](#screen-navigation)
5. [Focus Management](#focus-management)
6. [Common Pitfalls](#common-pitfalls)
7. [Testing Patterns](#testing-patterns)

---

## Worker Context Requirements

### Rule: `push_screen_wait()` Requires Worker Context

**Problem**: Calling `push_screen_wait()` directly in `on_mount()` or other lifecycle methods causes `NoActiveWorker` exception.

**Solution**: Wrap blocking screen operations in a worker using `run_worker()`.

### ✅ Correct Pattern

```python
class JdoApp(App):
    async def on_mount(self) -> None:
        """Handle app mount - initialize database and show home screen."""
        # Initialize database tables
        create_db_and_tables()
        
        # Always start at home screen
        await self.push_screen(HomeScreen())
        
        # Run startup flow in worker context (allows push_screen_wait)
        self.run_worker(self._startup_worker(), exclusive=True)
    
    async def _startup_worker(self) -> None:
        """Startup worker to handle AI configuration and draft checks.
        
        This runs in a worker context to allow push_screen_wait to work properly.
        """
        await self._ensure_ai_configured()
        
        # Check for pending drafts
        pending_draft = self._check_pending_drafts()
        if pending_draft:
            # This push_screen_wait call works because we're in a worker
            await self.push_screen(
                DraftRestoreScreen(pending_draft),
                self._on_draft_restore_decision,
            )
```

### ❌ Incorrect Pattern

```python
class JdoApp(App):
    async def on_mount(self) -> None:
        """This will fail with NoActiveWorker."""
        await self.push_screen(HomeScreen())
        
        # ❌ This will raise NoActiveWorker exception
        decision = await self.push_screen_wait(AiRequiredScreen())
```

### Worker Guidelines

| Operation | Requires Worker? | Notes |
|-----------|-----------------|-------|
| `push_screen()` | No | Non-blocking, safe anywhere |
| `push_screen_wait()` | **Yes** | Must be in worker context |
| `pop_screen()` | No | Non-blocking, safe anywhere |
| Database queries | No* | Fast queries OK in handlers, slow queries should use workers |
| AI calls | **Yes** | Always use workers for streaming/blocking AI calls |

*Note: Database session context managers are synchronous and generally fast enough for message handlers. For complex queries or bulk operations, use workers.

### Worker Cancellation

Use `exclusive=True` for startup/shutdown workers to ensure they complete:

```python
self.run_worker(self._startup_worker(), exclusive=True)
```

---

## Async Lifecycle Methods

### `on_mount()` - Initial Setup

Called once when widget/screen is first mounted.

**Use for:**
- Initial widget queries
- Focus setting
- Starting background workers
- **NOT for**: Long-running operations (use workers instead)

**Current Usage in JDO:**
- `JdoApp.on_mount()` - Initialize DB, push HomeScreen, start startup worker
- `ChatScreen.on_mount()` - Focus prompt input, display initial data, start risk detection worker
- Screens do NOT override `on_show()` or `on_resume()` currently

### ✅ Correct `on_mount()` Pattern

```python
async def on_mount(self) -> None:
    """Handle mount event."""
    # 1. Query widgets
    prompt = self.query_one("#prompt-input", PromptInput)
    
    # 2. Set focus
    prompt.focus()
    
    # 3. Load initial data (fast, synchronous)
    if self._initial_mode and self._initial_entity_type is not None:
        self._display_initial_data()
    
    # 4. Start background workers for async tasks
    self.run_worker(self._detect_and_show_risks(), name="risk_detection")
```

### Lifecycle Method Summary

| Method | When Called | Our Usage |
|--------|------------|-----------|
| `on_mount()` | Once on creation | DB init, focus, start workers |
| `on_show()` | Each time screen shown | Not used currently |
| `on_resume()` | When returning to screen | Not used currently |
| `on_hide()` | When screen hidden | Not used currently |
| `on_unmount()` | Once on removal | Not used currently |

**Design Decision**: We use `on_mount()` for all initialization and don't rely on `on_show()`/`on_resume()` since our screens are typically pushed once per user intent.

---

## Message Handling

### Message Bubbling

Messages bubble up from child widgets to parent containers to screens to the app.

**Pattern**: Screens post messages, App handles them.

### ✅ Message Flow Pattern

```python
# 1. Screen defines message classes
class HomeScreen(Screen):
    class ShowGoals(Message):
        """Request to show goals list."""
    
    def action_show_goals(self) -> None:
        """Handle 'g' key binding."""
        self.post_message(self.ShowGoals())

# 2. App handles the message
class JdoApp(App):
    def on_home_screen_show_goals(self, _message: HomeScreen.ShowGoals) -> None:
        """Handle show goals request from HomeScreen."""
        with get_session() as session:
            goals = list(session.exec(select(Goal)).all())
            goal_items = [
                {
                    "id": str(g.id),
                    "title": g.title,
                    "status": g.status.value,
                }
                for g in goals
            ]
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

### Message Handler Naming Convention

Textual automatically routes messages using the pattern:
- Message: `ScreenName.MessageName`
- Handler: `on_screen_name_message_name()`

Examples:
- `HomeScreen.ShowGoals` → `on_home_screen_show_goals()`
- `ChatScreen.Back` → `on_chat_screen_back()`
- `PromptInput.Submitted` → `on_prompt_input_submitted()`

### Message Best Practices

1. **Define messages as inner classes** of the screen/widget that posts them
2. **Use descriptive names** that indicate intent (e.g., `ShowGoals` not `GoalsButtonPressed`)
3. **Keep messages simple** - just data, no logic
4. **Handle in App or parent screen** - don't handle your own messages
5. **Document message purpose** in docstring

### Current Message Catalog

**HomeScreen Messages:**
- `NewChat` - Start new chat conversation
- `ShowGoals`, `ShowCommitments`, `ShowVisions`, `ShowMilestones` - Navigation to entity lists
- `ShowOrphans` - Show orphan commitments
- `ShowHierarchy` - Show hierarchy tree view
- `ShowIntegrity` - Show integrity dashboard
- `OpenSettings` - Open settings screen
- `StartTriage` - Start inbox triage mode

**ChatScreen Messages:**
- `Back` - Return to previous screen

**SettingsScreen Messages:**
- `Back` - Return to previous screen
- `ProviderChanged` - AI provider selection changed
- `AuthStatusChanged` - Authentication status changed

**Widget Messages:**
- `PromptInput.Submitted` - User submitted prompt text
- `HierarchyView.ItemSelected` - User selected item in hierarchy
- `DraftRestoreScreen.Restore/Discard` - Draft decision

---

## Screen Navigation

### Navigation Patterns

We use a simple screen stack model:
- `push_screen()` - Navigate to new screen
- `pop_screen()` - Return to previous screen
- `push_screen_wait()` - Navigate and wait for result (requires worker)

### ✅ Navigation Flow

```
HomeScreen (base)
  → push_screen(ChatScreen) → ChatScreen
    → push_screen(SettingsScreen) → SettingsScreen
      → pop_screen() → ChatScreen
    → pop_screen() → HomeScreen
```

### Screen Initialization with Data

**Pattern**: Use config objects for complex initialization.

```python
@dataclass
class ChatScreenConfig:
    """Configuration for ChatScreen initialization."""
    draft_id: UUID | None = None
    triage_mode: bool = False
    initial_mode: str | None = None
    initial_entity_type: str | None = None
    initial_data: list[dict[str, Any]] | dict[str, Any] | None = None

# Usage
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
- Groups related parameters
- Easier to extend without breaking API
- Self-documenting at call sites
- Reduces parameter count (9 → 4 in ChatScreen case)

### Screen Stack Management

**Guidelines**:
1. **HomeScreen is always base** - Never pop it
2. **Use messages for back navigation** - Let App handle pop_screen()
3. **Don't hold screen references** - Let Textual manage lifecycle
4. **Clean up in on_unmount()** if needed - We don't currently need this

### Current Navigation Handlers

All in `JdoApp`:
- `on_home_screen_new_chat()` - Push ChatScreen
- `on_home_screen_open_settings()` - Push SettingsScreen
- `on_chat_screen_back()` - Pop screen
- `on_settings_screen_back()` - Pop screen
- Navigation shortcuts (g/c/v/m/o/h/i) - Push ChatScreen with initial data

---

## Focus Management

### Focus Principles

1. **Set focus explicitly** in `on_mount()` or after major state changes
2. **Focus should be obvious** to the user (cursor visible, clear indication)
3. **Restore focus** after modals/dialogs if needed

### ✅ Focus Patterns

```python
async def on_mount(self) -> None:
    """Handle mount event."""
    # Focus the main input widget
    prompt = self.query_one("#prompt-input", PromptInput)
    prompt.focus()

def action_toggle_focus(self) -> None:
    """Toggle focus between chat and data panel (Tab key)."""
    prompt = self.query_one("#prompt-input", PromptInput)
    data_panel = self.query_one(DataPanel)
    
    if data_panel.has_focus_within:
        prompt.focus()
    else:
        data_panel.focus()
```

### Focus After Navigation

```python
def action_back(self) -> None:
    """Handle escape key - focus prompt or go back."""
    prompt = self.query_one("#prompt-input", PromptInput)
    
    if not prompt.has_focus:
        # First escape - focus prompt
        prompt.focus()
    else:
        # Second escape - go back
        self.post_message(self.Back())
```

### Current Focus Management

- **ChatScreen**: Focus prompt on mount, toggle focus with Tab
- **Escape key pattern**: First escape focuses prompt, second escape goes back
- **No focus restoration** after dialogs currently (not needed)

---

## OptionList Widget Patterns

### OptionList.highlighted Index Behavior

**Important**: `OptionList.highlighted` uses **selectable option indices only**, excluding separators.

When you add options with separators (using `None`), the `highlighted` property does NOT include separators in its index count:

```python
# Adding items with separators
option_list.add_option(Option("Chat", id="chat"))      # highlighted=0
option_list.add_option(None)                            # Separator (not counted)
option_list.add_option(Option("Goals", id="goals"))    # highlighted=1 (not 2!)
option_list.add_option(Option("Settings", id="settings"))  # highlighted=2

# To highlight "goals":
option_list.highlighted = 1  # NOT 2!
```

### ✅ Correct Pattern for NavSidebar

Pre-compute the mapping at initialization using the filtered items list:

```python
class NavSidebar(Widget):
    def __init__(self, ...):
        # Filter out separators for the item list
        self._nav_items = [item for item in NAV_ITEMS if item is not None]
        
        # Build item_id -> highlighted index mapping
        # OptionList.highlighted uses selectable indices (excludes separators)
        self._item_to_option_index: dict[str, int] = {
            item.id: idx for idx, item in enumerate(self._nav_items)
        }
    
    def set_active_item(self, item_id: str) -> None:
        """Set the active (highlighted) navigation item."""
        self.active_item = item_id
        if self._option_list is not None and item_id in self._item_to_option_index:
            self._option_list.highlighted = self._item_to_option_index[item_id]
```

### OptionList Methods Summary

| Property/Method | Behavior |
|-----------------|----------|
| `highlighted` | Index in selectable options only (excludes separators) |
| `option_count` | Count of selectable options only (excludes separators) |
| `get_option_at_index(i)` | Returns option at selectable index `i` |
| `add_option(None)` | Adds a visual separator (not selectable, not indexed) |

---

## Common Pitfalls

### 1. NoActiveWorker Exception

**Error**: `RuntimeError: There is no currently active worker`

**Cause**: Calling `push_screen_wait()` outside worker context

**Fix**: Wrap in `run_worker()`

```python
# ❌ Wrong
async def on_mount(self):
    result = await self.push_screen_wait(SomeScreen())

# ✅ Correct
async def on_mount(self):
    self.run_worker(self._async_flow(), exclusive=True)

async def _async_flow(self):
    result = await self.push_screen_wait(SomeScreen())
```

### 2. Accessing Workers in Streaming

**Pattern**: Use `get_current_worker()` to check for cancellation during streaming

```python
from textual.worker import get_current_worker

async def _do_ai_streaming(self, prompt: str) -> None:
    """Stream AI response."""
    worker = get_current_worker()
    
    async for chunk in stream_response(...):
        if worker.is_cancelled:
            break
        await self.chat_container.append_to_last(chunk)
```

### 3. Database Sessions in Handlers

**Pattern**: Use context managers, keep sessions short-lived

```python
# ✅ Correct - session scoped to handler
def on_home_screen_show_goals(self, _message: HomeScreen.ShowGoals) -> None:
    with get_session() as session:
        goals = list(session.exec(select(Goal)).all())
        # Process data...
    # Session closed automatically
    self.push_screen(ChatScreen(...))
```

### 4. Message Handler Return Values

**Important**: Message handlers don't return values. Use message data or screen callbacks.

```python
# ❌ Wrong - return value ignored
def on_some_message(self, message: SomeMessage) -> bool:
    return True  # This is ignored!

# ✅ Correct - use message data
class SomeMessage(Message):
    def __init__(self, result: bool) -> None:
        self.result = result
        super().__init__()
```

### 5. Screen Lifecycle Assumptions

**Don't assume** `on_show()` is called when you expect. We don't use `on_show()`/`on_resume()` currently.

**Do use** `on_mount()` for all initialization.

---

## Testing Patterns

### Textual Pilot Testing

Use `run_test()` context manager for TUI tests:

```python
async def test_navigation(home_app: type[App]) -> None:
    """Test navigation from HomeScreen."""
    async with home_app().run_test() as pilot:
        # Access widgets
        screen = pilot.app.query_one(HomeScreen)
        
        # Simulate key press
        await pilot.press("g")
        
        # Check screen changed
        assert isinstance(pilot.app.screen, ChatScreen)
```

### Testing Workers

Workers run in test mode synchronously (no actual threads):

```python
async def test_async_flow() -> None:
    """Test async worker flow."""
    async with TestApp().run_test() as pilot:
        # Trigger worker
        await pilot.press("enter")
        
        # Wait for worker completion
        await pilot.pause()
        
        # Verify result
        assert ...
```

### Snapshot Testing

For visual regression testing:

```python
def test_integrity_dashboard(snap_compare):
    """Test integrity dashboard renders correctly."""
    assert snap_compare("app.py", terminal_size=(120, 40))
```

### Testing Patterns We Use

1. **Unit tests** for business logic (models, services, commands)
2. **Integration tests** for database operations
3. **TUI tests** with Pilot for user interactions
4. **Snapshot tests** for visual components
5. **E2E tests** for full app lifecycle

---

## Reference Implementation Checklist

When creating new screens or features, verify:

- [ ] Worker context used for `push_screen_wait()`
- [ ] `on_mount()` sets focus appropriately
- [ ] Messages defined as inner classes
- [ ] Message handlers in App or parent screen
- [ ] Database sessions scoped to handlers
- [ ] Screen navigation uses config objects for complex init
- [ ] Tests cover happy path and error cases
- [ ] No blocking I/O in lifecycle methods
- [ ] Focus management tested manually

---

## Additional Resources

- [Textual Documentation](https://textual.textualize.io/)
- [Textual Discord](https://discord.gg/Enf6Z3qhVr)
- [JDO AGENTS.md](../AGENTS.md) - Project-specific coding guidelines

---

**Document Version**: 1.0  
**Last Updated**: 2025-12-18  
**Author**: JDO Development Team
