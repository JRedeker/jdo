## ADDED Requirements

### Requirement: OAuth HTTP Timeouts

The system SHALL enforce timeouts on all OAuth HTTP operations to prevent indefinite hangs.

#### Scenario: Timeout on token exchange
- **WHEN** `exchange_code()` makes an HTTP request to the token endpoint
- **THEN** the request has a 30-second timeout configured
- **AND** httpx.TimeoutException is raised if exceeded

#### Scenario: Timeout on token refresh
- **WHEN** `refresh_tokens()` makes an HTTP request to the token endpoint
- **THEN** the request has a 30-second timeout configured
- **AND** httpx.TimeoutException is raised if exceeded

### Requirement: OAuth HTTP Retry

The system SHALL retry OAuth HTTP operations on transient network failures using exponential backoff.

#### Scenario: Retry on connection error
- **WHEN** an OAuth HTTP request fails with httpx.ConnectError
- **THEN** the request is retried up to 3 times
- **AND** wait time increases exponentially with jitter (base 1s, max 10s)

#### Scenario: Retry on timeout error
- **WHEN** an OAuth HTTP request fails with httpx.TimeoutException
- **THEN** the request is retried up to 3 times with exponential backoff

#### Scenario: No retry on auth error
- **WHEN** an OAuth HTTP request fails with 401 Unauthorized
- **THEN** the error is NOT retried (auth failures are not transient)
- **AND** the original error is raised immediately

#### Scenario: All retries exhausted
- **WHEN** an OAuth HTTP request fails after all 3 retry attempts
- **THEN** the original exception type is re-raised (ConnectError or TimeoutException)
- **AND** the error can be caught and handled by the caller

### Requirement: Atomic Credential Storage

The system SHALL write credentials atomically to prevent corruption on interrupted writes.

#### Scenario: Atomic file write
- **WHEN** credentials are saved via `_write_store()`
- **THEN** data is written to a temporary file first
- **AND** the temp file is atomically renamed to the target path
- **AND** no partial writes can corrupt the credentials file

#### Scenario: Cleanup on write failure
- **WHEN** credential write fails (e.g., disk full)
- **THEN** the temporary file is cleaned up
- **AND** the original credentials file is unchanged
