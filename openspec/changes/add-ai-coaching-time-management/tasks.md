# Tasks: Add AI Coaching and Time Management System

## 1. Database Schema Changes

- [ ] 1.1 Add time fields to Task model (`estimated_hours`, `actual_hours`, `estimation_confidence`)
- [ ] 1.2 Create TaskHistoryEntry model with all required fields
- [ ] 1.3 Create database migration for new columns and table
- [ ] 1.4 Write unit tests for new model fields and validation
- [ ] 1.5 Verify migration applies cleanly to existing database

## 2. Task History Logging Service

- [ ] 2.1 Create TaskHistoryService with log_event method
- [ ] 2.2 Implement automatic logging on task creation
- [ ] 2.3 Implement automatic logging on task status changes
- [ ] 2.4 Implement logging with actual_hours on task completion
- [ ] 2.5 Write unit tests for history logging
- [ ] 2.6 Write integration tests verifying history survives task deletion

## 3. Commitment Time Rollup

- [ ] 3.1 Add computed property `total_estimated_hours` to Commitment
- [ ] 3.2 Add computed property `remaining_estimated_hours` to Commitment
- [ ] 3.3 Add computed property `completed_hours` to Commitment
- [ ] 3.4 Create helper function for time rollup queries (avoid N+1)
- [ ] 3.5 Write unit tests for rollup calculations
- [ ] 3.6 Write tests for edge cases (no estimates, mixed estimates)

## 4. Integrity Metrics Enhancement

- [ ] 4.1 Add `estimation_accuracy` calculation to IntegrityMetrics
- [ ] 4.2 Update composite_score formula with new weights (on_time: 0.35, estimation: 0.10, streak: 0.05)
- [ ] 4.3 Add minimum threshold check (5 tasks) for accuracy calculation
- [ ] 4.4 Update existing integrity tests for new formula
- [ ] 4.5 Write tests for estimation_accuracy calculation
- [ ] 4.6 Write tests for default accuracy with insufficient history

## 5. User Time Context

- [ ] 5.1 Add `available_hours_today` to JDODependencies or session state
- [ ] 5.2 Create method to get/set available hours within session
- [ ] 5.3 Create method to calculate hours_allocated from active tasks
- [ ] 5.4 Write unit tests for time context calculations

## 6. AI Tools Implementation

- [ ] 6.1 Implement `query_user_time_context` tool
- [ ] 6.2 Implement `query_task_history` tool with pattern analysis
- [ ] 6.3 Implement `query_commitment_time_rollup` tool
- [ ] 6.4 Implement `query_integrity_with_context` tool
- [ ] 6.5 Register all new tools in `register_tools()`
- [ ] 6.6 Write unit tests for each new tool
- [ ] 6.7 Write integration tests for tool outputs

## 7. AI System Prompt Enhancement

- [ ] 7.1 Replace SYSTEM_PROMPT with coaching-focused version
- [ ] 7.2 Add time-based pushback instructions
- [ ] 7.3 Add integrity-based coaching instructions
- [ ] 7.4 Add estimation coaching instructions
- [ ] 7.5 Test prompt with sample conversations (manual verification)

## 8. TUI Time Estimation Flow

- [ ] 8.1 Add estimate field to task creation draft panel
- [ ] 8.2 Implement natural language time parsing ("2 hours", "30 min")
- [ ] 8.3 Add actual hours prompt on task completion
- [ ] 8.4 Add "matched estimate" quick option
- [ ] 8.5 Write tests for time input parsing

## 9. TUI Available Hours Flow

- [ ] 9.1 Implement `/hours` command handler
- [ ] 9.2 Add available hours to ChatScreen state
- [ ] 9.3 Display hours in home screen or data panel
- [ ] 9.4 Add over-allocation warning display
- [ ] 9.5 Write tests for hours command

## 10. TUI Display Enhancements

- [ ] 10.1 Add time rollup to commitment detail view
- [ ] 10.2 Add estimation accuracy to integrity panel
- [ ] 10.3 Add time estimate column to task list
- [ ] 10.4 Add time-based risk warning to startup
- [ ] 10.5 Update snapshot tests for new displays

## 11. Command Handler Integration

- [ ] 11.1 Update task creation handler to log history
- [ ] 11.2 Update task status change handlers to log history
- [ ] 11.3 Update task completion to prompt for actual hours
- [ ] 11.4 Add AI coaching triggers to commitment creation
- [ ] 11.5 Write integration tests for full coaching flow

## 12. Documentation and Cleanup

- [ ] 12.1 Run full test suite and fix any failures
- [ ] 12.2 Run linter and type checker, fix issues
- [ ] 12.3 Verify migration works on fresh database
- [ ] 12.4 Manual testing of coaching scenarios

## Dependencies

- Tasks 1.x must complete before 2.x (history needs schema)
- Tasks 2.x must complete before 6.x (tools need history)
- Tasks 3.x can run parallel to 2.x
- Tasks 4.x can run parallel to 2.x and 3.x
- Tasks 5.x can run parallel to others
- Tasks 6.x requires 2.x, 3.x, 4.x, 5.x complete
- Tasks 7.x can start after 6.x
- Tasks 8.x, 9.x, 10.x can run parallel after 1.x
- Tasks 11.x requires 2.x, 6.x, 8.x, 9.x complete
- Task 12.x is final validation after all others

## Parallelizable Work

The following can be worked on simultaneously by different contributors:
- Group A: 1.x → 2.x → 6.x (data layer)
- Group B: 3.x, 4.x (calculations)
- Group C: 5.x, 7.x (AI context)
- Group D: 8.x, 9.x, 10.x (TUI)
