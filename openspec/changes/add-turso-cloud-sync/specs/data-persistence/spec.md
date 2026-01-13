## MODIFIED Requirements

### Requirement: Database Engine Management

The system SHALL provide a centralized SQLModel engine configured for SQLite, with optional libSQL support for cloud sync.

#### Scenario: Engine created on first access
- **WHEN** `get_engine()` is called for the first time
- **THEN** a SQLModel engine is created pointing to the configured database path

#### Scenario: Engine reuses existing connection
- **WHEN** `get_engine()` is called multiple times
- **THEN** the same engine instance is returned

#### Scenario: Engine uses WAL mode for SQLite
- **WHEN** the database engine is created
- **THEN** SQLite WAL mode is enabled for better concurrent access

#### Scenario: Engine uses libSQL when sync enabled
- **WHEN** `get_engine()` is called
- **AND** Turso sync is configured in settings
- **THEN** a libSQL engine is created with embedded replica support
- **AND** sync URL and auth token are configured from settings

#### Scenario: Engine falls back to SQLite when sync unavailable
- **WHEN** `get_engine()` is called
- **AND** Turso sync is configured but connection fails
- **THEN** logs a warning
- **AND** uses local replica in offline mode
