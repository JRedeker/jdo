# Design: TUI Core Architecture

## Context

The JDO TUI was built with `HomeScreen`, `ChatScreen`, and `SettingsScreen` as `Widget` subclasses. However, Textual's documentation clearly distinguishes between:

- **Screens**: Full-screen views that participate in navigation
- **Widgets**: Composable components within screens

This design document captures the architectural decisions for the TUI core layer.

## Goals / Non-Goals

### Goals
- Establish idiomatic Textual architecture patterns
- Enable proper screen stack navigation (`push_screen`/`pop_screen`)
- Define clear Widget vs Screen boundaries
- Support message-based communication between components
- Enable modal dialogs with `ModalScreen`

### Non-Goals
- Change any functional requirements (behavior stays the same)
- Add new features (this is architectural refactoring)
- Modify the AI agent or command handling

## Decisions

### Decision 1: Screen Subclasses for Navigation Targets

**What**: Convert `HomeScreen`, `ChatScreen`, `SettingsScreen` from `Widget` to `Screen` subclasses.

**Why**: 
- Textual's screen stack (`push_screen`/`pop_screen`) only works with `Screen` subclasses
- Screens participate in focus management, key bindings bubble correctly
- `SCREENS` dict registration enables name-based navigation

**Alternatives considered**:
- Keep as Widgets, use `mount()`/`remove()` for swapping
  - Rejected: Not idiomatic, loses screen stack benefits, requires manual focus management

### Decision 2: Widget Subclasses for Composable Components

**What**: Keep `ChatContainer`, `DataPanel`, `PromptInput`, `ChatMessage`, `HierarchyView` as `Widget` subclasses.

**Why**:
- These are reusable components composed within screens
- They don't represent navigable views
- Widgets can be mounted/unmounted within screens

### Decision 3: Message-Based Communication

**What**: Child components communicate with parent screens/app via `post_message()`.

**Why**:
- Decouples components from parent implementation
- Messages bubble up the DOM tree
- Parent handles routing/state changes

**Pattern**:
```python
# Widget defines message
class HomeScreen(Screen):
    class NewChat(Message):
        """User wants to start a new chat."""

    def action_new_chat(self) -> None:
        self.post_message(self.NewChat())

# App handles message
class JdoApp(App):
    def on_home_screen_new_chat(self) -> None:
        self.push_screen("chat")
```

### Decision 4: ModalScreen for Dialogs

**What**: Modal dialogs (OAuth, API Key, Draft Restore) use `ModalScreen` subclass.

**Why**:
- Prevents key bindings from bubbling to parent screen
- Built-in visual dimming of background screen
- `dismiss()` returns result to caller

**Pattern**:
```python
class DraftRestoreScreen(ModalScreen[str | None]):
    DEFAULT_CSS = """
    DraftRestoreScreen {
        align: center middle;
    }
    DraftRestoreScreen > Container {
        width: 60;
        height: auto;
        border: thick $background 80%;
        background: $surface;
    }
    """
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "restore":
            self.dismiss("restore")
        elif event.button.id == "discard":
            self.dismiss("discard")
```

### Decision 5: Screen Registration in SCREENS Dict

**What**: App registers all screens in `SCREENS` class variable.

**Why**:
- Enables name-based navigation: `self.push_screen("chat")`
- Screens are instantiated on-demand
- Consistent with Textual examples

**Pattern**:
```python
class JdoApp(App):
    SCREENS = {
        "home": HomeScreen,
        "chat": ChatScreen,
        "settings": SettingsScreen,
    }
    
    def on_mount(self) -> None:
        self.push_screen("home")
```

## Risks / Trade-offs

### Risk: Test Fixture Changes
- **Risk**: Existing tests create test apps that yield screens as widgets
- **Mitigation**: Update test fixtures to use `push_screen()` pattern or yield Screen in compose
- **Impact**: Low - mechanical changes, no logic changes

### Risk: CSS Selector Changes
- **Risk**: CSS selectors might break with Widget → Screen change
- **Mitigation**: CSS selectors work identically for Screen and Widget
- **Impact**: None expected - CSS is selector-based, not class-based

### Trade-off: Screen Instantiation
- **Trade-off**: Screens in `SCREENS` dict are classes, instantiated each `push_screen()`
- **Consideration**: For stateful screens, may need to use `install_screen()` for persistence
- **Decision**: Use dict registration for now, refactor if state persistence needed

## Migration Plan

### Phase 1: Refactor Screen Classes (Low Risk)
1. Change import from `textual.widget.Widget` to `textual.screen.Screen`
2. Change class inheritance
3. Verify CSS still applies
4. Run existing tests

### Phase 2: Update Test Fixtures (Low Risk)
1. Update test apps to use proper Screen testing patterns
2. Tests should pass with minimal changes

### Phase 3: Wire into JdoApp (Covered by `implement-jdo-app`)
1. Register screens in `SCREENS` dict
2. Implement message handlers
3. Add navigation bindings

### Rollback Plan
- Git revert to previous commit
- All changes are in-place refactors with no data migration

## Open Questions

None - architecture is well-documented in Textual docs and verified via Context7.
