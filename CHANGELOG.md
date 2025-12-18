# Changelog

All notable changes to JDO are documented here.

This changelog is automatically validated against `openspec/changes/archive/` by CI.
When a feature spec is archived, it should be added here and removed from `ROADMAP.yaml`.

## [Unreleased]

### Added
- Nothing yet

## [0.1.0] - 2025-12-17

Initial development release with core functionality.

### Added

#### Inbox & Capture
- **add-inbox-triage** (2025-12-18): CLI capture command (`jdo capture "text"`) and AI-powered triage classification

#### Core Infrastructure
- **refactor-core-libraries** (2025-12-16): Core infrastructure including paths, settings, database engine, and AI agent foundation
- **add-testing-infrastructure** (2025-12-16): pytest fixtures, coverage configuration, test markers, and CI setup

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
