## ADDED Requirements

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
