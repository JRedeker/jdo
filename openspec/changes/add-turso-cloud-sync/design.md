# Design: Turso Cloud Sync

## Context

jdo is a local-first CLI app using SQLite via SQLModel. Users have requested multi-device sync to access their commitments from different machines. This is a **future feature** - not an immediate priority.

### Stakeholders
- End users wanting multi-device access
- Developer (maintainability, minimal complexity)

### Constraints
- Must remain local-first (offline capable)
- Minimal user setup friction
- Low/no cost for typical usage
- SQLModel/SQLAlchemy compatibility required

## Goals / Non-Goals

### Goals
- Enable opt-in cloud sync with minimal configuration
- Preserve local-first behavior (reads never blocked by network)
- Simple conflict resolution (last-write-wins)
- Easy onboarding (`jdo sync setup` interactive flow)

### Non-Goals
- Real-time collaboration (multiple users editing same data)
- Complex conflict resolution (CRDTs, merge strategies)
- Self-hosted sync server option (may add later)
- Automatic sync without user opt-in

## Decisions

### Decision 1: Use Turso with Embedded Replicas

**Choice**: Turso (libSQL) with embedded replica mode

**Rationale**:
- SQLite-compatible (libSQL is a SQLite fork)
- Embedded replicas provide true offline-first with automatic sync
- Generous free tier (9GB, 500M reads, 25M writes/month)
- Official Python SDK with SQLAlchemy support

**Alternatives considered**:
| Option | Pros | Cons |
|--------|------|------|
| Litestream + S3 | Cheap, standard SQLite | One-way only, no multi-device |
| Cloudflare D1 | Free, global | Designed for Workers, not CLI apps |
| PowerSync | Real-time sync | Requires Postgres backend |
| cr-sqlite | True CRDT sync | DIY infrastructure, complex |

### Decision 2: Last-Write-Wins Conflict Resolution

**Choice**: Simple timestamp-based last-write-wins

**Rationale**:
- jdo is single-user per account
- Conflicts rare (user unlikely to edit same item on two devices simultaneously)
- Simple to understand and debug
- Can upgrade to smarter resolution later if needed

### Decision 3: Opt-in via CLI Setup Command

**Choice**: Explicit `jdo sync setup` command to enable

**Rationale**:
- No surprise cloud connections
- User controls when data leaves their machine
- Clear onboarding flow with Turso account creation guidance

### Decision 4: Credential Storage Pattern

**Choice**: Reuse existing auth store pattern (`auth.json`)

**Rationale**:
- Consistent with AI provider auth
- Already handles secure storage (0600 permissions)
- Users familiar with the pattern

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        jdo CLI                               │
├─────────────────────────────────────────────────────────────┤
│  SyncService                                                 │
│  ├─ setup()      - Interactive Turso setup                  │
│  ├─ status()     - Show sync state                          │
│  ├─ force_sync() - Manual sync trigger                      │
│  └─ disable()    - Revert to local-only                     │
├─────────────────────────────────────────────────────────────┤
│  Database Engine (src/jdo/db/engine.py)                     │
│  ├─ Local mode:  sqlite:///jdo.db (current)                 │
│  └─ Sync mode:   libsql:///local.db?syncUrl=...&authToken=. │
├─────────────────────────────────────────────────────────────┤
│  Settings (src/jdo/config/settings.py)                      │
│  ├─ turso_enabled: bool                                     │
│  ├─ turso_db_url: str | None                                │
│  └─ turso_auth_token: str | None (via auth store)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Turso Cloud    │
                    │  (libSQL)       │
                    └─────────────────┘
```

### Sync Flow

1. **Write path**: Local write → Commit → Background sync to Turso
2. **Read path**: Always local (instant)
3. **Startup**: Pull latest from Turso → Merge into local replica
4. **Conflict**: Last write timestamp wins

## Data Model Changes

No schema changes required. Existing `updated_at` timestamps on all models provide last-write-wins resolution.

## Risks / Trade-offs

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Turso service outage | Low | Medium | Local replica continues working; sync resumes when available |
| libSQL Python SDK instability | Medium | Medium | Pin to stable version; can fall back to local-only |
| User data loss on conflict | Low | High | Warn on first sync if local differs from cloud; offer backup |
| Turso pricing changes | Low | Low | Free tier is generous; can migrate to Litestream if needed |

## Migration Plan

### New Users
1. `jdo sync setup` guides through Turso account creation
2. Creates cloud database, stores credentials
3. Future sessions auto-sync

### Existing Users (Local Data)
1. `jdo sync setup` detects existing local database
2. Prompts: "Upload existing data to cloud? [Y/n]"
3. If yes: full upload, then switch to sync mode
4. If no: start fresh in cloud (local data preserved separately)

### Rollback
1. `jdo sync disable` reverts to local-only mode
2. Local replica becomes the source of truth
3. Cloud data preserved but not synced

## Open Questions

1. **Sync frequency**: Sync after every write, or batch with delay?
   - Recommendation: After every write (Turso handles batching)

2. **Multi-account support**: One Turso account per user, or shared?
   - Recommendation: One account per user (simplest)

3. **Initial sync UX**: Show progress for large databases?
   - Recommendation: Yes, with Rich progress bar

4. **Offline indicator**: Show sync status in REPL prompt?
   - Recommendation: Optional, subtle indicator (e.g., cloud icon when synced)
