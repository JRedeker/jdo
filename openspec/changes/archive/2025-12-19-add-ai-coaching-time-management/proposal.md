# Change: Add AI Coaching and Time Management System

## Why

Users currently have no mechanism to prevent over-commitment. The AI acts as a passive assistant rather than an active coach that pushes back when users take on more than they can realistically accomplish. Without time estimates on tasks and available hours tracking, users can't make informed decisions about what to commit to. Additionally, there's no historical record of task completion patterns, so the AI can't learn from past performance to provide calibrated coaching.

The integrity protocol exists but lacks the data foundation to deliver meaningful pushback. Users need:
1. Time estimates for every task to enable workload math
2. Daily available hours to compare against commitments
3. Task completion history to identify estimation patterns
4. AI coaching that actively pushes back on over-commitment
5. Credit for completing stakeholder notifications while preserving the learning history

## What Changes

### New Capabilities
- **Time Estimation System**: Add estimated/actual hours to tasks with rollup to commitments
- **Task History Logging**: Audit log of all task lifecycle events for AI learning
- **User Daily Context**: Track available hours per day for workload comparison
- **AI Coaching Tools**: New tools for querying time context, history, and integrity

### Modified Capabilities
- **Task Model**: Add `estimated_hours`, `actual_hours`, `estimation_confidence` fields
- **Commitment Model**: Add computed properties for time rollups
- **AI Provider**: Enhanced system prompt with coaching behaviors, new tools
- **Integrity**: Add `estimation_accuracy` metric (10% weight), preserve at-risk history
- **TUI Chat**: Add available hours prompts, time estimate flows

### Key Behaviors
- AI SHALL ask "How many hours do you have available today?" at session start
- AI SHALL request time estimates for every task created
- AI SHALL warn when total estimates exceed available hours
- AI SHALL reference integrity score when coaching (e.g., "Your grade is C+...")
- AI SHALL acknowledge stakeholder notifications positively while preserving history
- Task history SHALL be immutable and queryable by AI for pattern analysis

## Impact

### Affected Specs
- `task` - Add time fields and history logging trigger
- `commitment` - Add time rollup properties
- `ai-provider` - New coaching system prompt and 4 new tools
- `tui-chat` - Add time estimation prompts and available hours flow
- `integrity` - New spec for integrity protocol with estimation_accuracy metric

### Affected Code
- `src/jdo/models/task.py` - Add fields
- `src/jdo/models/commitment.py` - Add computed properties
- `src/jdo/models/task_history.py` - New model
- `src/jdo/models/user_context.py` - New model (or service)
- `src/jdo/models/integrity_metrics.py` - Add estimation_accuracy
- `src/jdo/ai/agent.py` - Enhanced system prompt
- `src/jdo/ai/tools.py` - 4 new tools
- `src/jdo/integrity/service.py` - History queries, estimation accuracy
- `src/jdo/commands/handlers.py` - Time prompts, history logging
- `migrations/` - New migration for schema changes

### Database Changes
- Add columns to `tasks`: `estimated_hours`, `actual_hours`, `estimation_confidence`
- Add new table: `task_history` for audit logging
- Add new table or config: `user_context` for daily available hours

### Risk Assessment
- **Low Risk**: Additive changes, no breaking changes to existing behavior
- **Migration**: Simple column additions, backward compatible
- **Testing**: Requires comprehensive tests for coaching scenarios
