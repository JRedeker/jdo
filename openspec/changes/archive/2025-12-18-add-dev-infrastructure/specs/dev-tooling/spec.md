# dev-tooling Specification

## Purpose
Define pre-commit hooks and developer tooling configuration to enforce code quality standards before commits, ensuring consistent formatting, linting, and type checking.

## ADDED Requirements

### Requirement: Pre-commit Framework

The system SHALL use pre-commit framework for git hook management.

#### Scenario: Install pre-commit hooks
- **WHEN** developer runs `pre-commit install`
- **THEN** git hooks are installed in `.git/hooks/`
- **AND** hooks run automatically on `git commit`

#### Scenario: Run all hooks manually
- **WHEN** developer runs `pre-commit run --all-files`
- **THEN** all configured hooks run against the entire codebase

#### Scenario: Skip hooks when needed
- **WHEN** developer runs `git commit --no-verify`
- **THEN** pre-commit hooks are bypassed

### Requirement: Ruff Linting Hook

The system SHALL enforce ruff linting rules via pre-commit.

#### Scenario: Auto-fix lint violations
- **WHEN** a staged file has auto-fixable lint violations
- **THEN** ruff automatically fixes them
- **AND** the commit proceeds if all violations are fixed

#### Scenario: Block commit on unfixable violations
- **WHEN** a staged file has lint violations that cannot be auto-fixed
- **THEN** the commit is blocked
- **AND** violation details are displayed

### Requirement: Ruff Formatting Hook

The system SHALL enforce ruff formatting via pre-commit.

#### Scenario: Auto-format staged files
- **WHEN** a staged file has formatting issues
- **THEN** ruff-format automatically reformats the file
- **AND** the file is re-staged

### Requirement: Type Checking Hook

The system SHALL enforce type checking via pre-commit.

#### Scenario: Type check passes
- **WHEN** all staged Python files pass pyrefly type checking
- **THEN** the commit proceeds

#### Scenario: Type check fails
- **WHEN** a staged file has type errors
- **THEN** the commit is blocked
- **AND** type error details are displayed

#### Scenario: Type check runs on all files
- **WHEN** pyrefly hook runs
- **THEN** it checks `src/` directory (not just staged files)
- **AND** this ensures cross-file type consistency

### Requirement: Standard Hooks

The system SHALL include standard pre-commit hooks for basic hygiene.

#### Scenario: Trailing whitespace removal
- **WHEN** a staged file has trailing whitespace
- **THEN** it is automatically removed

#### Scenario: End of file newline
- **WHEN** a staged file is missing a final newline
- **THEN** one is automatically added

#### Scenario: Large file prevention
- **WHEN** a staged file exceeds 500KB
- **THEN** the commit is blocked with a warning

#### Scenario: YAML validation
- **WHEN** a staged YAML file has syntax errors
- **THEN** the commit is blocked with error details

### Requirement: Configuration File

The system SHALL provide a `.pre-commit-config.yaml` configuration file.

#### Scenario: Config file exists
- **WHEN** developer clones the repository
- **THEN** `.pre-commit-config.yaml` exists at the repository root

#### Scenario: Config specifies hook versions
- **WHEN** pre-commit runs
- **THEN** it uses pinned versions for reproducibility
