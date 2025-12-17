# vision Specification

## Purpose
Define the Vision domain model representing long-term aspirational outcomes with vivid narratives and measurable success metrics, including quarterly review cadence and goal associations.
## Requirements
### Requirement: Vision Model

The system SHALL provide a `Vision` SQLModel with the following validated fields:
- `id` (UUID): Unique identifier, auto-generated
- `title` (str): Short inspiring headline, required, non-empty
- `timeframe` (str | None): When this vision is realized (e.g., "5 years", "2027", "Q4 2026")
- `narrative` (str): Vivid description of the future state, required, non-empty
- `metrics` (list[str]): How will you know you've achieved this? Stored as JSON array
- `why_it_matters` (str | None): Why this vision ignites passion
- `status` (VisionStatus enum): One of `active`, `achieved`, `evolved`, `abandoned`; defaults to `active`
- `next_review_date` (date): When the user should next review this vision; defaults to 90 days from creation (non-nullable)
- `last_reviewed_at` (datetime | None): When the user last reviewed this vision
- `created_at` (datetime): Auto-set on creation, timezone-aware (EST default)
- `updated_at` (datetime): Auto-updated on modification, timezone-aware (EST default)

#### Scenario: Create vision with required fields
- **WHEN** user creates a Vision with title and narrative
- **THEN** a valid Vision is created with status="active", next_review_date set to 90 days from now, and auto-generated timestamps

#### Scenario: Create vision with metrics
- **WHEN** user creates a Vision with metrics=["Metric 1", "Metric 2"]
- **THEN** the metrics are stored as a JSON array in the database

#### Scenario: Reject vision without title
- **WHEN** user creates a Vision with an empty title
- **THEN** SQLModel validation raises an error

#### Scenario: Reject vision without narrative
- **WHEN** user creates a Vision with an empty narrative
- **THEN** SQLModel validation raises an error

### Requirement: Vision Status Transitions

The system SHALL enforce valid status transitions for Visions.

#### Scenario: Mark vision achieved
- **WHEN** user changes Vision status from "active" to "achieved"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Mark vision evolved
- **WHEN** user changes Vision status from "active" to "evolved"
- **THEN** the status is updated and updated_at is refreshed
- **AND** AI prompts: "What has this vision evolved into? Would you like to create a new vision?"

#### Scenario: Mark vision abandoned
- **WHEN** user changes Vision status from "active" to "abandoned"
- **THEN** the status is updated and updated_at is refreshed

#### Scenario: Reactivate vision
- **WHEN** user changes Vision status from "achieved", "evolved", or "abandoned" back to "active"
- **THEN** the status is updated, next_review_date is recalculated, and updated_at is refreshed

### Requirement: Vision Persistence

The system SHALL persist Vision entities to SQLite with full CRUD operations via SQLModel sessions.

#### Scenario: Save and retrieve vision
- **WHEN** user saves a new Vision via a database session
- **THEN** the Vision is persisted to SQLite and can be retrieved by id

#### Scenario: List visions with filters
- **WHEN** user queries visions with status filter (e.g., status="active")
- **THEN** the system returns only visions matching the filter criteria

#### Scenario: Delete vision without goals
- **WHEN** user deletes a Vision that has no associated goals
- **THEN** the Vision is removed from the database

#### Scenario: Prevent deletion of vision with goals
- **WHEN** user attempts to delete a Vision that has associated Goals
- **THEN** the system raises an error: "Cannot delete vision with linked goals. Unlink or delete the goals first."

### Requirement: Vision Review System

The system SHALL proactively prompt users to review their visions on a quarterly cadence.

#### Scenario: Calculate default review date
- **WHEN** a new Vision is created without explicit next_review_date
- **THEN** next_review_date is set to 90 days (quarterly) from creation date

#### Scenario: Prompt for vision review
- **WHEN** user opens the app and a Vision has next_review_date <= today
- **THEN** AI prompts: "Your vision '[title]' is due for review. Would you like to reflect on it now?"

#### Scenario: Complete vision review
- **WHEN** user completes a vision review
- **THEN** last_reviewed_at is set to current timestamp and next_review_date is set to 90 days from now

#### Scenario: Snooze vision review
- **WHEN** user declines to review a vision when prompted
- **THEN** the prompt does not repeat until the next app session or until user explicitly requests review

### Requirement: Vision-Goal Relationship

The system SHALL support optional association between Goals and Visions.

#### Scenario: Query goals for vision
- **WHEN** user queries for goals linked to a specific Vision
- **THEN** the system returns all Goals with vision_id matching the Vision's id

#### Scenario: Vision without goals
- **WHEN** a Vision has no linked Goals
- **THEN** the Vision exists independently and AI suggests: "This vision has no goals yet. Would you like to create a goal to work toward it?"

#### Scenario: Orphan goals warning
- **WHEN** user views goals and some have no vision_id
- **THEN** AI can surface these as "goals without a guiding vision" for user consideration

### Requirement: Vision Metrics Tracking

The system SHALL support storing and displaying measurable success criteria for visions.

#### Scenario: Store multiple metrics
- **WHEN** user creates a Vision with metrics ["Publish 1 book", "Give 10 talks", "Train 100 practitioners"]
- **THEN** all metrics are stored in the JSON array and displayed in the data panel

#### Scenario: Empty metrics allowed
- **WHEN** user creates a Vision without specifying metrics
- **THEN** the Vision is created with an empty metrics array

#### Scenario: Display metrics in view
- **WHEN** user views a Vision
- **THEN** metrics are displayed as a bulleted list in the data panel

### Requirement: Vision AI Assistance

The system SHALL use AI to help users articulate vivid, inspiring visions.

#### Scenario: Vision creation guidance
- **WHEN** user starts creating a vision
- **THEN** AI guides with prompts like: "Describe a day in your life when this vision is realized. What do you see, hear, feel?"

#### Scenario: Narrative refinement
- **WHEN** user provides a brief or vague narrative
- **THEN** AI offers to expand it: "Let's make this more vivid. What specific evidence would tell you this vision is real?"

#### Scenario: Metrics suggestion
- **WHEN** user has a narrative but no metrics
- **THEN** AI suggests: "How will you know you've achieved this? Let's define 2-3 measurable outcomes."

