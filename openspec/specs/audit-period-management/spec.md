## ADDED Requirements

### Requirement: Configure audit months

The system SHALL allow administrators to configure specific months when compliance audits must be completed via `config.yaml`.

#### Scenario: Valid audit months configuration
- **WHEN** config.yaml contains `compliance.audit_months: [3, 9]`
- **THEN** system recognizes March and September as audit months

#### Scenario: Multiple audit months
- **WHEN** config.yaml contains `compliance.audit_months: [3, 5, 9, 11]`
- **THEN** system recognizes all four months as audit months

#### Scenario: Invalid month value
- **WHEN** config.yaml contains month value outside 1-12 range
- **THEN** system fails to start with clear error message indicating invalid month

### Requirement: Map upload to audit period

The system SHALL automatically determine which audit period an upload belongs to based on the upload date and configured audit months.

#### Scenario: Upload during audit month
- **WHEN** current date is 2026-03-15 and audit_months is [3, 9]
- **THEN** upload maps to audit period "2026-03"

#### Scenario: Upload between audit months (forward)
- **WHEN** current date is 2026-04-10 and audit_months is [3, 9]
- **THEN** upload maps to next audit period "2026-09"

#### Scenario: Upload after last audit month of year
- **WHEN** current date is 2026-10-05 and audit_months is [3, 9]
- **THEN** upload maps to first audit period of next year "2027-03"

#### Scenario: Upload before first audit month of year
- **WHEN** current date is 2026-01-15 and audit_months is [3, 9]
- **THEN** upload maps to first audit period of current year "2026-03"

### Requirement: Audit period directory structure

The system SHALL store reports in directories named by audit period in format `YYYY-MM` where MM is the audit month.

#### Scenario: Directory creation for audit period
- **WHEN** upload maps to audit period "2026-03"
- **THEN** reports stored under `./reports/2026-03/`

#### Scenario: System directory within audit period
- **WHEN** webserver01 (user admin) uploads to audit period "2026-03"
- **THEN** reports stored in `./reports/2026-03/webserver01-admin/`

#### Scenario: Multiple uploads to same period
- **WHEN** webserver01 uploads on 2026-02-10 and 2026-03-15 (both map to 2026-03)
- **THEN** second upload overwrites first in `./reports/2026-03/webserver01-admin/`

### Requirement: Prevent future audit period storage

The system SHALL never create directories for audit periods in the future.

#### Scenario: Current period only
- **WHEN** current date is 2026-03-15 and upload maps to 2026-03
- **THEN** directory `./reports/2026-03/` is created

#### Scenario: Next period allowed
- **WHEN** current date is 2026-04-15 and upload maps to 2026-09 (future but next period)
- **THEN** directory `./reports/2026-09/` is created

#### Scenario: No arbitrary future periods
- **WHEN** system determines audit period
- **THEN** only current or next audit period directories are created, never beyond

### Requirement: Compliance enabled flag

The system SHALL support enabling/disabling compliance tracking via configuration.

#### Scenario: Compliance enabled
- **WHEN** config.yaml contains `compliance.enabled: true`
- **THEN** system uses audit-period-based storage and compliance dashboard

#### Scenario: Compliance disabled
- **WHEN** config.yaml contains `compliance.enabled: false` or compliance section is absent
- **THEN** system uses legacy date-based storage (`hostname-username-YYYYMMDD/`)

#### Scenario: Backwards compatibility
- **WHEN** existing config.yaml has no compliance section
- **THEN** system operates in legacy mode without errors
