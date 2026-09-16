# Report Storage

## Purpose
Defines how submitted tar archives are named on disk, under which filenames
accepted reports are written, and how files written by earlier client
generations remain readable.

## Requirements

### Requirement: Tar archive filename format

The system SHALL save uploaded tar archives with a "honeybadger-" prefix followed by timestamp.

#### Scenario: Tar archive saved with honeybadger prefix
- **WHEN** client uploads tar archive via POST /submit-tar
- **THEN** system saves file as `honeybadger-{YYYYMMDD-HHMMSS}.tar.gz`

#### Scenario: Example tar filename
- **WHEN** tar uploaded on 2026-03-30 at 14:29:31
- **THEN** saved as `honeybadger-20260330-142931.tar.gz`

#### Scenario: Download preserves meaningful prefix
- **WHEN** user downloads tar from compliance dashboard
- **THEN** filename includes directory and honeybadger prefix (e.g., `lobos-wtoorren-honeybadger-20260330-142931.tar.gz`)

#### Scenario: Multiple tar uploads same system same day
- **WHEN** system uploads multiple tar archives within same audit period
- **THEN** each saved with unique timestamp ensuring no overwrites

### Requirement: Backward compatibility with existing tar files

The system SHALL continue to serve existing tar files with "submission-" prefix.

#### Scenario: Old tar files remain accessible
- **WHEN** tar file exists with old naming `submission-20260315-120000.tar.gz`
- **THEN** file continues to be downloadable via dashboard

#### Scenario: Dashboard shows both naming conventions
- **WHEN** system directory contains mix of submission-* and honeybadger-* tar files
- **THEN** dashboard displays most recent tar file regardless of naming convention

### Requirement: Store fastfetch reports under a fixed filename

The system SHALL write an accepted fastfetch report to `fastfetch-report.json`
within the system directory for the audit period.

#### Scenario: Fastfetch report saved
- **WHEN** a client submits a report of type `fastfetch` for `lobos-wtoorren`
  in audit period 2026-09
- **THEN** the file is written to
  `reports/2026-09/lobos-wtoorren/fastfetch-report.json`

#### Scenario: Same-period resubmission overwrites
- **WHEN** the same system submits a fastfetch report twice within one audit
  period
- **THEN** the second submission overwrites the first

### Requirement: Retain legacy neofetch files

The system SHALL leave existing `neofetch-report.json` files on disk unchanged.

#### Scenario: Legacy file present
- **WHEN** a system directory contains `neofetch-report.json` from a previous
  client generation
- **THEN** the file is neither renamed nor deleted

#### Scenario: Legacy file not used as system information
- **WHEN** the compliance cache is rebuilt and a directory contains only
  `neofetch-report.json` as system information
- **THEN** the system reports OS type "unknown" and does not count the file
  toward completeness

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

### Requirement: Record the audit's findings with the submission

The submission record SHALL carry the findings the client determined, and SHALL
keep the inventory document whole alongside them.

#### Scenario: Findings written into the record
- **WHEN** a submission carries an asset inventory
- **THEN** `submission.json` holds its findings, beside the asset ID, owner and
  class already recorded there

#### Scenario: The whole document is kept
- **WHEN** an inventory is stored
- **THEN** the complete document is kept, so fields the server does not model
  today are not discarded

#### Scenario: Unknown schema version
- **WHEN** an inventory declares a `schema_version` the server does not
  recognise
- **THEN** the document is stored and the fields the server understands are
  used; the submission is not refused

#### Scenario: Malformed inventory
- **WHEN** an inventory cannot be parsed
- **THEN** it is logged and skipped, and the submission is stored as it
  otherwise would be

#### Scenario: No inventory present
- **WHEN** a submission carries no inventory
- **THEN** the record holds none, and the submission is otherwise unaffected
