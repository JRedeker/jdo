# cloud-sync Specification

## Purpose

Define the optional cloud synchronization capability using Turso (libSQL) for multi-device data access. This is an opt-in feature that preserves local-first behavior while enabling automatic sync when configured.

## ADDED Requirements

### Requirement: Sync Service

The system SHALL provide a SyncService for managing cloud synchronization state and operations.

#### Scenario: Check sync status when disabled
- **WHEN** `SyncService.status()` is called
- **AND** sync is not configured
- **THEN** returns status indicating sync is disabled

#### Scenario: Check sync status when enabled
- **WHEN** `SyncService.status()` is called
- **AND** sync is configured and connected
- **THEN** returns status including last sync timestamp and connection state

#### Scenario: Force manual sync
- **WHEN** `SyncService.force_sync()` is called
- **AND** sync is enabled
- **THEN** immediately syncs with Turso cloud
- **AND** returns success/failure status

### Requirement: Sync Setup Flow

The system SHALL provide an interactive setup flow for configuring Turso cloud sync.

#### Scenario: First-time setup
- **WHEN** user runs `jdo sync setup`
- **AND** no Turso credentials exist
- **THEN** displays guidance for creating Turso account
- **AND** prompts for database URL and auth token
- **AND** validates connection before saving
- **AND** stores credentials securely in auth store

#### Scenario: Setup with existing local data
- **WHEN** user runs `jdo sync setup`
- **AND** local database contains data
- **THEN** prompts user to confirm upload of existing data
- **AND** if confirmed, migrates local data to cloud on first sync

#### Scenario: Setup validation failure
- **WHEN** user provides invalid Turso credentials
- **THEN** displays clear error message
- **AND** does not save credentials
- **AND** allows retry

### Requirement: Sync Disable

The system SHALL allow users to disable cloud sync and revert to local-only mode.

#### Scenario: Disable sync
- **WHEN** user runs `jdo sync disable`
- **AND** sync is currently enabled
- **THEN** reverts to local-only database mode
- **AND** preserves local replica data
- **AND** removes Turso credentials from auth store

#### Scenario: Disable when already disabled
- **WHEN** user runs `jdo sync disable`
- **AND** sync is not enabled
- **THEN** displays message that sync is already disabled

### Requirement: Offline Resilience

The system SHALL continue operating when cloud sync is enabled but network is unavailable.

#### Scenario: Read while offline
- **WHEN** Turso cloud is unreachable
- **AND** user performs read operations
- **THEN** reads succeed from local replica
- **AND** no error is displayed to user

#### Scenario: Write while offline
- **WHEN** Turso cloud is unreachable
- **AND** user performs write operations
- **THEN** writes succeed to local replica
- **AND** changes queue for sync when connection restores

#### Scenario: Sync resumes on reconnection
- **WHEN** network connectivity is restored
- **AND** there are pending local changes
- **THEN** changes automatically sync to cloud
- **AND** remote changes sync to local replica

### Requirement: Conflict Resolution

The system SHALL resolve sync conflicts using last-write-wins based on timestamps.

#### Scenario: Concurrent edits on different devices
- **WHEN** the same record is edited on two devices
- **AND** both devices sync
- **THEN** the edit with the later `updated_at` timestamp wins
- **AND** the earlier edit is overwritten

#### Scenario: No conflict on different records
- **WHEN** different records are edited on different devices
- **AND** both devices sync
- **THEN** all changes are preserved without conflict

### Requirement: CLI Commands

The system SHALL provide CLI commands for sync management.

#### Scenario: Sync setup command
- **WHEN** user runs `jdo sync setup`
- **THEN** interactive setup flow begins

#### Scenario: Sync status command
- **WHEN** user runs `jdo sync status`
- **THEN** displays current sync configuration and state

#### Scenario: Sync disable command
- **WHEN** user runs `jdo sync disable`
- **THEN** disables sync and reverts to local-only

#### Scenario: Sync now command
- **WHEN** user runs `jdo sync now`
- **AND** sync is enabled
- **THEN** forces immediate sync with cloud
