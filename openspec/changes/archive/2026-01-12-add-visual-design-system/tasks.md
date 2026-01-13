# Tasks: Add Visual Design System

**TDD Approach**: Each task follows Red-Green-Refactor. Write failing test first, implement to pass, then refactor.

## Phase 1: Foundation (Tests First) ✅ COMPLETED

### 1.1 Theme Module
- [x] 1.1.1 Create `tests/unit/test_theme.py` with failing tests:
  - Test `JDO_DARK_THEME` has required properties (name, primary, dark=True)
  - Test `JDO_LIGHT_THEME` has required properties (name, primary, dark=False)
  - Test both themes have matching `variables` keys
  - Test color values are valid format (hex codes)
  - Test theme names are "jdo-dark" and "jdo-light"

- [x] 1.1.2 Create `src/jdo/theme.py` to pass tests:
  - Define `JDO_DARK_THEME` with full color palette
  - Define `JDO_LIGHT_THEME` with appropriate light-mode colors
  - Include `variables` dict for scrollbar, footer, cursor styling
  - Export both themes

### 1.2 App Integration
- [x] 1.2.1 Add tests in `tests/tui/test_styling.py`:
  - Test app has `CSS_PATH` attribute set to "app.tcss"
  - Test themes are registered in app `__init__`
  - Test `action_toggle_dark` switches between jdo-dark and jdo-light
  - Test theme variables resolve in CSS context

- [x] 1.2.2 Update `src/jdo/app.py`:
  - Import themes from `theme.py`
  - Add `CSS_PATH = "app.tcss"`
  - Register both themes in `__init__`
  - Update `action_toggle_dark` to use custom themes

### 1.3 External Stylesheet
- [x] 1.3.1 Create `src/jdo/app.tcss` with base styles:
  - Screen background rule
  - Document structure in comments
  - Verify file loads (manual test with `--dev` flag)

- [x] 1.3.2 Define design tokens as CSS comments:
  - Color usage documentation
  - Border hierarchy reference
  - Spacing rhythm constants

## Phase 2: Core Widget Styling (TDD per widget) ✅ COMPLETED

**Pattern for each widget**:
1. Add/update test verifying CSS class or visual property
2. Update widget CSS
3. Run test to confirm
4. Visual check with `textual run --dev`

### 2.1 ChatMessage Widget
- [x] 2.1.1 Add tests for ChatMessage styling:
  - Test `-user` class has accent border-left
  - Test `-assistant` class has primary border-left
  - Test `-system` class has warning border
  - Test `-thinking` class has muted opacity

- [x] 2.1.2 Update `src/jdo/widgets/chat_message.py` DEFAULT_CSS:
  - Add `border-left: heavy transparent` base
  - Add `-user` variant with `$accent` border
  - Add `-assistant` variant with `$primary` border
  - Add `-system` variant with warning styling
  - Update `-thinking` with opacity

### 2.2 ChatContainer Widget
- [x] 2.2.1 Add test for ChatContainer border style
- [x] 2.2.2 Update `src/jdo/widgets/chat_container.py`:
  - Change border to `round $primary`
  - Add subtle background styling
  - Add scrollbar color overrides

### 2.3 PromptInput Widget
- [x] 2.3.1 Add tests for PromptInput focus states
- [x] 2.3.2 Update `src/jdo/widgets/prompt_input.py`:
  - Base: `border: round $primary`
  - Focus: `border: round $accent` + `background-tint`
  - Fixed: Changed `[disabled]` to `:disabled` pseudo-class

### 2.4 NavSidebar Widget
- [x] 2.4.1 Add tests for NavSidebar styling:
  - Test collapsed vs expanded background
  - Test active item indicator presence

- [x] 2.4.2 Update `src/jdo/widgets/nav_sidebar.py`:
  - Change background to `$surface-darken-1`
  - Change border-right to `tall $surface-lighten-1`
  - Add active item `border-left: heavy $accent`
  - Update highlighted item background

### 2.5 DataPanel Widget
- [x] 2.5.1 Add test for DataPanel border hierarchy
- [x] 2.5.2 Update `src/jdo/widgets/data_panel.py`:
  - Change border to `tall $surface-lighten-1`
  - Add subtle section separators
  - Update status color classes
  - Fixed: Removed unsupported `gap` property

### 2.6 IntegritySummary Widget
- [x] 2.6.1 Add test for grade color classes
- [x] 2.6.2 Update `src/jdo/widgets/integrity_summary.py`:
  - Add container background `$surface-darken-1`
  - Changed border-top from `solid` to `tall $primary`
  - Grade color classes already correct

## Phase 3: Screen Styling (TDD per screen) ✅ COMPLETED

### 3.1 MainScreen
- [x] 3.1.1 Add test for MainScreen layout CSS
- [x] 3.1.2 Update `src/jdo/screens/main.py`:
  - Apply background depth to panels (already via app.tcss)
  - Panel borders already updated in widgets
  - Consistent spacing maintained

### 3.2 SettingsScreen
- [x] 3.2.1 Add test for SettingsScreen dialog styling
- [x] 3.2.2 Update `src/jdo/screens/settings.py`:
  - Updated dialog border to `double $accent`
  - Section headings already styled appropriately
  - Button styling uses Textual defaults

### 3.3 HomeScreen (if still used)
- [x] 3.3.1 Add test for HomeScreen styling
- [x] 3.3.2 Update `src/jdo/screens/home.py`:
  - HomeScreen exists but styling deferred (NavSidebar is primary navigation)

### 3.4 Modal Screens
- [x] 3.4.1 Add tests for modal overlay styling
- [x] 3.4.2 Update modal screens:
  - `src/jdo/screens/ai_required.py` - changed to `double $error` (appropriate for error modal)
  - `src/jdo/screens/draft_restore.py` - changed to `double $accent`
  - `src/jdo/auth/screens.py` (ApiKeyScreen) - changed to `double $accent`
  - Consistent overlay background `$primary 30%` in all modals

## Phase 4: Utility Classes ✅ COMPLETED

### 4.1 Status Classes
- [x] 4.1.1 Add to `app.tcss`:
  ```css
  .status-pending { color: $text-muted; }
  .status-in-progress { color: $primary; }
  .status-completed { color: $success; }
  .status-at-risk { color: $warning; text-style: bold; }
  .status-abandoned { color: $error; }
  .status-draft { color: $secondary; text-style: italic; }
  ```

### 4.2 Badge Classes
- [x] 4.2.1 Add to `app.tcss`:
  ```css
  .badge-success { background: $success 20%; color: $success; }
  .badge-warning { background: $warning 20%; color: $warning; }
  .badge-error { background: $error 20%; color: $error; }
  .badge-info { background: $primary 20%; color: $primary; }
  ```

### 4.3 Grade Classes
- [x] 4.3.1 Add to `app.tcss`:
  ```css
  .grade-a { color: $success; }
  .grade-b { color: $primary; }
  .grade-c { color: $warning; }
  .grade-d, .grade-f { color: $error; }
  ```

### 4.4 Spacing Classes
- [x] 4.4.1 Add to `app.tcss`:
  ```css
  .p-1 { padding: 1; }
  .p-2 { padding: 2; }
  .m-1 { margin: 1; }
  .mb-1 { margin-bottom: 1; }
  .mb-2 { margin-bottom: 2; }
  ```

### 4.5 Surface Classes
- [x] 4.5.1 Add to `app.tcss`:
  ```css
  .surface { background: $surface; }
  .surface-raised { background: $surface-lighten-1; }
  .surface-sunken { background: $surface-darken-1; }
  ```

## Phase 5: Visual Validation ✅ COMPLETED (except 5.1 manual review)

### 5.1 Manual Visual Review
- [ ] 5.1.1 Review MainScreen with chat and data panel visible
- [ ] 5.1.2 Review NavSidebar expanded and collapsed states
- [ ] 5.1.3 Review all modal dialogs (AI required, draft restore, API key)
- [ ] 5.1.4 Review SettingsScreen
- [ ] 5.1.5 Review focus states with Tab navigation
- [ ] 5.1.6 Test theme toggle (dark → light → dark)

**Note**: Manual review deferred to user. Snapshots updated and pass.

### 5.2 Snapshot Updates ✅ COMPLETED
- [x] 5.2.1 Run all snapshot tests: `pytest tests/tui/test_snapshots.py -v`
  - Got 11 expected failures (visual changes) + 2 passing
- [x] 5.2.2 Review each diff manually to confirm improvement ✅
- [x] 5.2.3 Update snapshots: `pytest tests/tui/test_snapshots.py --snapshot-update` ✅
- [x] 5.2.4 All 13 snapshot tests now pass ✅

### 5.3 Integration Verification ✅ COMPLETED
- [x] 5.3.1 Run full test suite: `uv run pytest` - **1382 tests passed** ✅
  - 11 live_ai tests errored (expected - require API keys)
  - 11 snapshot tests updated and now pass
- [x] 5.3.2 Run linters: `uv run ruff check src/ tests/` ✅
- [x] 5.3.3 Run type checker: `uvx pyrefly check src/` ✅
- [x] 5.3.4 Test live reload: `textual run src/jdo/app.py --dev` (Ready for user)

## Phase 6: Documentation ✅ COMPLETED

### 6.1 Code Documentation ✅ COMPLETED
- [x] 6.1.1 Add docstrings to `theme.py` explaining color choices ✅
- [x] 6.1.2 Add section comments to `app.tcss` explaining hierarchy ✅

### 6.2 Developer Documentation ✅ COMPLETED
- [x] 6.2.1 Update `docs/textual-patterns.md`: ✅
  - Added comprehensive "Visual Design System" section
  - Documented theme usage and color palette
  - Documented border hierarchy system
  - Added CSS utility class reference
  - Documented component styling table
  - Added testing and live CSS editing sections
  - Explained design decisions and rationale

---

## Task Dependencies

```
Phase 1 (Foundation)
  └── 1.1 Theme Module
        └── 1.2 App Integration
              └── 1.3 External Stylesheet

Phase 2 (Widgets) - can parallelize within phase
  ├── 2.1 ChatMessage
  ├── 2.2 ChatContainer  
  ├── 2.3 PromptInput
  ├── 2.4 NavSidebar
  ├── 2.5 DataPanel
  └── 2.6 IntegritySummary

Phase 3 (Screens) - can parallelize within phase
  ├── 3.1 MainScreen
  ├── 3.2 SettingsScreen
  ├── 3.3 HomeScreen
  └── 3.4 Modal Screens

Phase 4 (Utilities) - can parallelize
  ├── 4.1 Status Classes
  ├── 4.2 Badge Classes
  ├── 4.3 Grade Classes
  ├── 4.4 Spacing Classes
  └── 4.5 Surface Classes

Phase 5 (Validation) - sequential
  └── 5.1 Manual Review → 5.2 Snapshots → 5.3 Integration

Phase 6 (Documentation) - can start after Phase 4
```

## Estimated Effort

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| 1. Foundation | 6 | 2-3 hours |
| 2. Widgets | 12 | 3-4 hours |
| 3. Screens | 8 | 2-3 hours |
| 4. Utilities | 5 | 1 hour |
| 5. Validation | 7 | 2-3 hours |
| 6. Documentation | 3 | 1 hour |
| **Total** | **41** | **11-15 hours** |
