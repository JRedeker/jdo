# Change: Fix Navigation Messages and Review Textual Implementation

## Why

HomeScreen has keyboard shortcuts (g, c, v, m, o, h, i) that post messages like `ShowGoals`, `ShowCommitments`, `ShowVisions`, etc., but JdoApp only handles `NewChat` and `OpenSettings`. This means **6 out of 10 keyboard shortcuts are broken** - users can't view their data.

Additionally, after implementing the integrity protocol and fixing the worker context bug, we should perform a comprehensive review of our Textual implementation against official documentation to:
1. Ensure all async patterns follow Textual best practices
2. Verify worker usage is correct throughout the codebase
3. Document any known limitations or Textual-specific patterns
4. Create a reference guide for future Textual development

## What Changes

### 1. Fix Navigation Message Handlers (Critical UX Bug)

Add missing message handlers in `JdoApp` for:
- `ShowGoals` - Navigate to ChatScreen with goals list in DataPanel
- `ShowCommitments` - Navigate to ChatScreen with commitments list
- `ShowVisions` - Navigate to ChatScreen with visions list  
- `ShowMilestones` - Navigate to ChatScreen with milestones list
- `ShowOrphans` - Navigate to ChatScreen with orphan commitments
- `ShowHierarchy` - Navigate to ChatScreen with hierarchy tree view
- `ShowIntegrity` - Navigate to ChatScreen with integrity dashboard

### 2. Comprehensive Textual Implementation Review

Review and document:
- Worker context usage (`run_worker`, `push_screen_wait`)
- Async lifecycle methods (`on_mount`, `on_show`, `on_resume`)
- Message handling patterns
- Screen navigation patterns
- Focus management
- Data panel state coordination

### 3. Documentation

Create `/docs/textual-patterns.md` with:
- Textual best practices we follow
- Common pitfalls and how we avoid them
- Worker context requirements and examples
- Message handling conventions
- Testing patterns for Textual apps

## Impact

### Affected Specs
- `jdo-app` (modified - add navigation message handlers)
- `tui-core` (modified - document Textual patterns and conventions)

### Affected Code
- `src/jdo/app.py` - Add 7 message handlers for navigation
- `docs/textual-patterns.md` - New documentation file
- Tests may need updates to cover new navigation paths

### Breaking Changes
None - this fixes broken functionality and adds documentation.

## Dependencies

- Requires existing HomeScreen message classes (already implemented)
- Requires existing DataPanel modes (already implemented)
- All required UI components already exist - just need wiring

## Acceptance Criteria

1. **Navigation Works**: All keyboard shortcuts on HomeScreen navigate to correct views
   - 'g' shows goals list
   - 'c' shows commitments list
   - 'v' shows visions list
   - 'm' shows milestones list
   - 'o' shows orphan commitments
   - 'h' shows hierarchy tree
   - 'i' shows integrity dashboard

2. **Textual Review Complete**: Documentation covers all async patterns and worker usage

3. **Tests Pass**: All existing tests continue to pass, navigation paths tested

4. **Documentation**: `docs/textual-patterns.md` created with clear examples
