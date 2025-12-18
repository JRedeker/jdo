## MODIFIED Requirements

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

#### Scenario: Query triage items
- **WHEN** `get_triage_items(session)` is called
- **THEN** Draft records with `entity_type=UNKNOWN` are returned ordered by `created_at` ascending (FIFO)

#### Scenario: Count triage items
- **WHEN** `get_triage_count(session)` is called
- **THEN** the count of Draft records with `entity_type=UNKNOWN` is returned

## ADDED Requirements

### Requirement: EntityType UNKNOWN Value

The system SHALL support an UNKNOWN entity type for items needing triage.

#### Scenario: UNKNOWN in EntityType enum
- **WHEN** a Draft is created for triage
- **THEN** `entity_type` can be set to `EntityType.UNKNOWN`

#### Scenario: UNKNOWN drafts excluded from normal draft restore
- **WHEN** the app checks for pending drafts on startup
- **THEN** drafts with `entity_type=UNKNOWN` are not included in the restore prompt
- **AND** they are handled separately via the triage system
