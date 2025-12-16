# data-persistence Specification

## Purpose
TBD - created by archiving change refactor-core-libraries. Update Purpose after archive.
## Requirements
### Requirement: Database Engine Management

The system SHALL provide a centralized SQLModel engine configured for SQLite.

#### Scenario: Engine created on first access
- **WHEN** `get_engine()` is called for the first time
- **THEN** a SQLModel engine is created pointing to the configured database path

#### Scenario: Engine reuses existing connection
- **WHEN** `get_engine()` is called multiple times
- **THEN** the same engine instance is returned

#### Scenario: Engine uses WAL mode for SQLite
- **WHEN** the database engine is created
- **THEN** SQLite WAL mode is enabled for better concurrent access

### Requirement: Session Context Manager

The system SHALL provide a context manager for database sessions with automatic transaction handling.

#### Scenario: Session commits on success
- **WHEN** code block within `with get_session() as session:` completes without exception
- **THEN** the transaction is automatically committed

#### Scenario: Session rolls back on exception
- **WHEN** an exception is raised within `with get_session() as session:`
- **THEN** the transaction is rolled back and the exception is re-raised

#### Scenario: Session is closed after use
- **WHEN** `with get_session() as session:` block exits
- **THEN** the session is properly closed and resources released

### Requirement: Schema Management

The system SHALL manage database schema creation and updates.

#### Scenario: Create tables on first run
- **WHEN** `create_db_and_tables()` is called and database does not exist
- **THEN** all SQLModel tables are created with proper schema

#### Scenario: Preserve existing data
- **WHEN** `create_db_and_tables()` is called and database exists with data
- **THEN** existing tables and data are preserved

#### Scenario: Tables created in correct order
- **WHEN** `create_db_and_tables()` is called
- **THEN** tables are created respecting foreign key dependencies (Stakeholder before Commitment, etc.)

### Requirement: CRUD Operations

The system SHALL support standard CRUD operations through SQLModel sessions.

#### Scenario: Create entity
- **WHEN** `session.add(entity)` and `session.commit()` are called
- **THEN** the entity is persisted to the database with auto-generated id

#### Scenario: Read entity by id
- **WHEN** `session.get(Model, id)` is called with a valid id
- **THEN** the entity is returned with all fields populated

#### Scenario: Read entity not found
- **WHEN** `session.get(Model, id)` is called with non-existent id
- **THEN** None is returned

#### Scenario: Update entity
- **WHEN** entity fields are modified and `session.commit()` is called
- **THEN** changes are persisted and `updated_at` is refreshed

#### Scenario: Delete entity
- **WHEN** `session.delete(entity)` and `session.commit()` are called
- **THEN** the entity is removed from the database

### Requirement: Query Support

The system SHALL support SQLModel query patterns for filtering and ordering.

#### Scenario: Filter by field value
- **WHEN** `session.exec(select(Model).where(Model.field == value))`
- **THEN** only matching entities are returned

#### Scenario: Filter by multiple conditions
- **WHEN** `session.exec(select(Model).where(Model.a == x, Model.b == y))`
- **THEN** entities matching all conditions are returned

#### Scenario: Order results
- **WHEN** `session.exec(select(Model).order_by(Model.field))`
- **THEN** results are returned in ascending order by field

#### Scenario: Limit results
- **WHEN** `session.exec(select(Model).limit(n))`
- **THEN** at most n entities are returned

### Requirement: Relationship Loading

The system SHALL support eager and lazy loading of relationships. Note: `selectinload` requires importing from SQLAlchemy directly (`from sqlalchemy.orm import selectinload`), not from SQLModel.

#### Scenario: Lazy load relationship
- **WHEN** accessing `commitment.stakeholder` without explicit join
- **THEN** the related Stakeholder is loaded on first access

#### Scenario: Eager load with selectinload
- **WHEN** query uses `options(selectinload(Commitment.tasks))` with `selectinload` imported from `sqlalchemy.orm`
- **THEN** related Tasks are loaded in a single additional query

#### Scenario: Access relationship after session close
- **WHEN** relationship is not loaded and session is closed
- **THEN** accessing the relationship raises DetachedInstanceError

