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
