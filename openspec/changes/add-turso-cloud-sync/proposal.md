# Change: Add Turso Cloud Sync for Multi-Device Support

> **Status**: Future feature - not an immediate need

## Why

Users want to access their commitments, goals, and tasks across multiple devices. Currently, jdo uses a local SQLite database with no cloud backup or synchronization capability. Turso (libSQL) provides a SQLite-compatible cloud database with embedded replicas that enable:

1. **Multi-device sync**: Data automatically syncs between devices
2. **Offline-first**: Local replica works without connectivity
3. **Fast reads**: All reads are local (sub-millisecond)
4. **Low cost**: Generous free tier (9GB storage, 500M reads/month)

## What Changes

- Add new `cloud-sync` capability for Turso integration
- **MODIFY** `data-persistence` to support libSQL connection when cloud sync is enabled
- **MODIFY** `app-config` to add Turso-related settings
- Add CLI commands for cloud sync setup (`jdo sync setup`, `jdo sync status`)
- Add authentication flow for Turso (similar to AI provider auth)

### Dependencies

- `libsql-experimental` - Python libSQL client with embedded replica support
- Turso account (free tier available)

### Migration Path

- Existing local-only users are unaffected (opt-in feature)
- First sync uploads local database to Turso
- Conflict resolution: last-write-wins (simple, predictable)

## Impact

- **Affected specs**:
  - `cloud-sync` (NEW) - Core sync capability
  - `data-persistence` - Engine configuration changes
  - `app-config` - New settings for Turso
- **Affected code**:
  - `src/jdo/db/engine.py` - libSQL connection support
  - `src/jdo/config/settings.py` - Turso settings
  - `src/jdo/sync/` (NEW) - Sync service and CLI
  - `src/jdo/auth/` - Turso credential storage
