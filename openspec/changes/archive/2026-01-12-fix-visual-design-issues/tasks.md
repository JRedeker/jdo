# Implementation Tasks

## 1. Research & Analysis
- [x] 1.1 Review current collapsed sidebar CSS implementation
- [x] 1.2 Test collapsed sidebar behavior to confirm issue
- [x] 1.3 Research Textual best practices for maintaining visual state in collapsed views
- [x] 1.4 Identify appropriate visual indicator for collapsed active item (background color, border, icon)

## 2. Fix Collapsed Sidebar Active Indicator
- [x] 2.1 Design visual solution that works in collapsed state
- [x] 2.2 Update CSS in `src/jdo/widgets/nav_sidebar.py` for collapsed highlighted items
- [x] 2.3 Ensure sufficient contrast and accessibility
- [x] 2.4 Write/update snapshot tests for collapsed sidebar states

## 3. Fix Binding Description
- [x] 3.1 Update binding in `src/jdo/app.py` from "Toggle Dark Mode" to "Toggle Theme"
- [x] 3.2 Verify binding displays correctly in UI (covered via `tests/tui/test_app.py`)

## 4. Add Documentation
- [x] 4.1 Add comment in `src/jdo/app.py` clarifying CSS_PATH resolution
- [x] 4.2 Add comment in `src/jdo/app.tcss` documenting universal selector performance consideration

## 5. Testing & Validation
- [x] 5.1 Run full test suite: `uv run pytest` (note: live AI E2E tests currently error due to unsupported `JDO_AI_PROVIDER=anthropic`)
- [x] 5.2 Manual testing of collapsed sidebar with different themes (covered via snapshot apps + updated snapshots)
- [x] 5.3 Visual regression testing with snapshot updates
- [x] 5.4 Run linting: `uv run ruff check --fix src/ tests/`
- [x] 5.5 Run formatting: `uv run ruff format src/ tests/`
- [x] 5.6 Run type checking: `uvx pyrefly check src/`
