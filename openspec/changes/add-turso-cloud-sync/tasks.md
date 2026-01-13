# Tasks: Add Turso Cloud Sync

> **Status**: Future feature - implementation deferred

## Phase 1: Foundation

- [ ] 1.1 Add `libsql-experimental` dependency to `pyproject.toml`
- [ ] 1.2 Create `src/jdo/sync/` module structure
- [ ] 1.3 Add Turso settings to `JDOSettings` (`turso_enabled`, `turso_db_url`)
- [ ] 1.4 Add Turso auth token storage to auth store (`turso` provider key)

## Phase 2: Database Engine Integration

- [ ] 2.1 Modify `get_engine()` to detect sync mode and create libSQL connection
- [ ] 2.2 Create `get_sync_engine()` function for libSQL with embedded replica
- [ ] 2.3 Add sync URL and auth token configuration to engine setup
- [ ] 2.4 Ensure WAL mode and foreign keys work with libSQL
- [ ] 2.5 Write integration tests for both local and sync engine modes

## Phase 3: Sync Service

- [ ] 3.1 Create `SyncService` class with setup/status/disable methods
- [ ] 3.2 Implement `sync setup` interactive flow (Turso account guidance)
- [ ] 3.3 Implement `sync status` command (show sync state, last sync time)
- [ ] 3.4 Implement `sync disable` command (revert to local-only)
- [ ] 3.5 Add manual `sync now` command for forced sync

## Phase 4: CLI Commands

- [ ] 4.1 Add `jdo sync` command group to CLI
- [ ] 4.2 Implement `jdo sync setup` subcommand
- [ ] 4.3 Implement `jdo sync status` subcommand
- [ ] 4.4 Implement `jdo sync disable` subcommand
- [ ] 4.5 Add sync status indicator to REPL (optional)

## Phase 5: Migration & Safety

- [ ] 5.1 Implement local-to-cloud migration flow (upload existing data)
- [ ] 5.2 Add backup prompt before first sync
- [ ] 5.3 Implement conflict detection logging (for debugging)
- [ ] 5.4 Add graceful degradation when Turso is unreachable

## Phase 6: Testing & Documentation

- [ ] 6.1 Write unit tests for SyncService
- [ ] 6.2 Write integration tests for sync scenarios
- [ ] 6.3 Add sync documentation to README
- [ ] 6.4 Test offline behavior (network disconnect scenarios)

## Dependencies

- Phase 2 depends on Phase 1
- Phase 3 depends on Phase 2
- Phase 4 depends on Phase 3
- Phase 5 depends on Phase 3
- Phase 6 can run in parallel with Phases 4-5

## Notes

This is a **future feature**. Implementation should only begin when:
1. Multi-device sync becomes a priority
2. libSQL Python SDK matures (currently experimental)
3. User demand justifies the added complexity
