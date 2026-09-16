# Audit Period Management

## Purpose
Defines how the server groups submitted reports into audit periods: which
months count as audit months, how an upload date maps to a period, how those
periods are laid out on disk, and how compliance tracking is enabled.

## Requirements

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

The system SHALL determine the audit period of a submission as the most recent
configured audit month at or before the submission date.

#### Scenario: Upload during audit month
- **WHEN** a submission arrives 2026-09-15 and audit_months is [3, 9]
- **THEN** it belongs to audit period "2026-09"

#### Scenario: Upload between audit months (forward)
- **WHEN** a submission arrives 2026-04-10 and audit_months is [3, 9]
- **THEN** it belongs to audit period "2026-03", the round that was open, and
  is NOT filed forward to "2026-09"

#### Scenario: Upload after last audit month of year
- **WHEN** a submission arrives 2026-10-02 and audit_months is [3, 9]
- **THEN** it belongs to audit period "2026-09", so a round running past its
  audit month keeps its late submissions

#### Scenario: Upload before first audit month of year
- **WHEN** a submission arrives 2026-02-10 and audit_months is [3, 9]
- **THEN** it belongs to audit period "2025-09"

### Requirement: Audit period directory structure

In compliance mode the system SHALL NOT encode the audit period in any
filesystem path; the period of a submission SHALL be computed from its
timestamp. Legacy mode, which has no audit periods, is unaffected.

#### Scenario: Directory creation for audit period
- **WHEN** a submission is stored
- **THEN** no directory is created for its audit period; the path contains the
  hardware serial and the submission timestamp

#### Scenario: System directory within audit period
- **WHEN** a submission from serial `PF50L2MR` arrives at 2026-09-15 13:25:34
- **THEN** it is written to `reports/submissions/PF50L2MR/2026-09-15T13-25-34/`

#### Scenario: Multiple uploads to same period
- **WHEN** one asset submits twice within a single audit period
- **THEN** both submissions are stored in their own timestamped directories and
  neither overwrites the other

#### Scenario: Legacy mode has no audit periods
- **WHEN** `compliance.enabled` is false
- **THEN** no audit period is computed or stored, and directories continue to
  be named `hostname-username-YYYYMMDD`

#### Scenario: Reconfiguring audit months reclassifies history
- **WHEN** `audit_months` changes from [3, 9] to [3, 6, 9, 12]
- **THEN** existing submissions are reclassified on the next index rebuild
  without any file being moved

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

### Requirement: Classify submissions as on time or late

The system SHALL record whether a submission arrived within the scan window of
its round or after it.

#### Scenario: Within the scan window
- **WHEN** a submission arrives 2026-09-15 and belongs to period 2026-09
- **THEN** it is classified `on_time`

#### Scenario: After the scan window
- **WHEN** a submission arrives after the audit month and its grace period, but
  before the next round opens
- **THEN** it is classified `late` and still counts toward the round

#### Scenario: Late classification is reported
- **WHEN** a round contains late submissions
- **THEN** the round view marks those assets as covered late, with the date

### Requirement: Scan window and coverage window

A round SHALL have a scan window, being its audit month extended by the
configured grace period, and a coverage window running until the next round
opens.

#### Scenario: Grace period governs both boundaries
- **WHEN** `grace_weeks` is configured
- **THEN** it defines both the on_time/late boundary for a submission and the
  scan window used to decide whether an asset belongs to the round

#### Scenario: Coverage window extends beyond the scan window
- **WHEN** round 2026-09 is evaluated
- **THEN** its scan window is September plus the grace period, while its
  coverage window runs until the 2027-03 round opens
