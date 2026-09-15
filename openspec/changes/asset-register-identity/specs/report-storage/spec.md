## MODIFIED Requirements

### Requirement: Store one record per submission

In compliance mode the system SHALL store each submission in its own
timestamped directory under the hardware serial, and SHALL NOT overwrite an
existing record. Legacy mode storage is unaffected.

#### Scenario: Submission stored under serial and timestamp
- **WHEN** a submission with serial `PF50L2MR` arrives at 2026-09-15 13:25:34
- **THEN** it is written to
  `reports/submissions/PF50L2MR/2026-09-15T13-25-34/`

#### Scenario: Repeat submission in the same round
- **WHEN** the same asset submits twice within one audit round
- **THEN** both records exist side by side and neither is overwritten

#### Scenario: Tar retained alongside extracted reports
- **WHEN** a submission is stored
- **THEN** the original tar archive is kept in the record directory together
  with the extracted reports

#### Scenario: Unmatched submission
- **WHEN** a submission does not resolve to a register entry
- **THEN** it is written to
  `reports/unmatched/<hostname>-<username>/<timestamp>/`

#### Scenario: Legacy mode unchanged
- **WHEN** `compliance.enabled` is false
- **THEN** storage continues to use `hostname-username-YYYYMMDD/` directories
  and none of the serial-keyed layout applies

### Requirement: Freeze the existing archive

The system SHALL treat `reports/2026-03/` as a read-only archive of the closed
spring 2026 round.

#### Scenario: Archive is never written
- **WHEN** any submission is received
- **THEN** nothing is written under `reports/2026-03/`

#### Scenario: Archive is readable
- **WHEN** the index is rebuilt
- **THEN** archive directories are indexed as records of period 2026-03 without
  a serial, and are excluded from register reconciliation

## ADDED Requirements

### Requirement: Download filename follows the register convention

The system SHALL serve a submission's tar archive under the proof file naming
convention used by the ISO reporting sheet.

#### Scenario: Matched asset download
- **WHEN** a user downloads the tar for TARI-00023, owner Wouter van der
  Toorren, submitted 2026-09-15
- **THEN** the browser receives it as
  `TARI-00023-2026-09-15-wouter.toorren.tar.gz`

#### Scenario: Unmatched submission download
- **WHEN** a user downloads the tar for an unmatched submission
- **THEN** the filename falls back to hostname, username and timestamp
