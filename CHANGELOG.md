# Changelog

All notable changes to JDO are documented here.

This changelog is automatically validated against `openspec/changes/archive/` by CI.
When a feature spec is archived, it should be added here and removed from `ROADMAP.yaml`.

## [Unreleased]

### Added

#### Navigation & UX
- **fix-navigation-and-review-textual** (2025-12-19): Fixed all HomeScreen keyboard shortcuts (g/c/v/m/o/h/i), added ChatScreenConfig pattern, comprehensive Textual patterns documentation

#### Testing
- **add-ai-driven-uat** (2025-12-19): AI-driven UAT framework with scenario definitions and mock agent testing

#### AI Integration
- **wire-ai-to-chat** (2025-12-19): Connected PydanticAI agent to ChatScreen with streaming responses and tool invocation
- **persist-handler-results** (2025-12-19): Wired command handlers to database persistence with confirmation flow
- **add-ai-coaching-time-management** (2025-12-19): AI time coaching with /hours command and task duration tracking

## [0.1.0] - 2025-12-17

Initial development release with core functionality.

### Added

#### Inbox & Capture
- **add-inbox-triage** (2025-12-18): CLI capture command (`jdo capture "text"`) and AI-powered triage classification

#### Integrity & Accountability
- **add-integrity-protocol** (2025-12-18): Honor-Your-Word protocol with at-risk status, cleanup plans, integrity metrics dashboard, and automated notification workflows

#### Core Infrastructure
- **refactor-core-libraries** (2025-12-16): Core infrastructure including paths, settings, database engine, and AI agent foundation
- **add-testing-infrastructure** (2025-12-16): pytest fixtures, coverage configuration, test markers, and CI setup
- **add-dev-infrastructure** (2025-12-18): Structured logging with Loguru, custom exception hierarchy, pre-commit hooks, Sentry observability, and Alembic database migrations

#### Authentication
- **add-provider-auth** (2025-12-16): OAuth PKCE + API key authentication for Anthropic, OpenAI, and OpenRouter providers

#### Domain Models
- **add-core-domain-models** (2025-12-16): Stakeholder, Goal, Commitment, and Task models with full CRUD operations
- **add-vision-milestone-hierarchy** (2025-12-16): Vision and Milestone models with review tracking and hierarchy relationships
- **add-recurring-commitments** (2025-12-17): RecurringCommitment model with pattern calculator and instance generator

#### User Interface
- **add-conversational-tui** (2025-12-16): ChatScreen, DataPanel, and HierarchyView widgets for Textual TUI
- **add-tui-core** (2025-12-16): Core TUI architecture and screen management
- **implement-jdo-app** (2025-12-16): Main application entry point and screen routing

#### Other
- **update-goal-vision-focus** (2025-12-17): Enhanced goal and vision focus tracking

---

## Format

Each entry should reference the archived spec directory name and include:
- **spec-name** (date): Brief description of what was implemented

Specs are archived to: `openspec/changes/archive/YYYY-MM-DD-spec-name/`
