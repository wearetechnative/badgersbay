## ADDED Requirements

### Requirement: Accept OS-Type header

The system SHALL accept an optional X-OS-Type header to identify the operating system of the client.

#### Scenario: OS type provided
- **WHEN** client sends header `X-OS-Type: ubuntu`
- **THEN** system accepts and stores os_type metadata

#### Scenario: OS type not provided
- **WHEN** client omits X-OS-Type header
- **THEN** system continues processing without error (header is optional)

#### Scenario: OS type in success response
- **WHEN** upload succeeds with X-OS-Type header
- **THEN** success response includes os_type in metadata

### Requirement: Calculate target audit period

The system SHALL calculate which audit period an upload belongs to based on upload date and configured audit months.

#### Scenario: Upload during audit month
- **WHEN** upload received on 2026-03-15 and audit_months is [3, 9]
- **THEN** target audit period is "2026-03"

#### Scenario: Upload between audit months
- **WHEN** upload received on 2026-04-10 and audit_months is [3, 9]
- **THEN** target audit period is "2026-09"

#### Scenario: Upload after last audit month
- **WHEN** upload received on 2026-10-05 and audit_months is [3, 9]
- **THEN** target audit period is "2027-03"

### Requirement: Include audit period in response

The system SHALL include the target audit period in the success response.

#### Scenario: Success response with audit period
- **WHEN** upload succeeds in compliance mode
- **THEN** response includes `"audit_period": "2026-03"`

#### Scenario: Legacy mode response
- **WHEN** upload succeeds in legacy mode (compliance disabled)
- **THEN** response does not include audit_period field

## MODIFIED Requirements

### Requirement: Success response includes storage path

The system SHALL return the storage path in success responses, reflecting the storage mode.

#### Scenario: Compliance mode success response
- **WHEN** upload succeeds in compliance mode
- **THEN** response path is `./reports/2026-03/laptop-SN001-alice/lynis-report.json`

#### Scenario: Legacy mode success response
- **WHEN** upload succeeds in legacy mode
- **THEN** response path is `./reports/laptop-SN001-alice-20260316/lynis-report.json`
