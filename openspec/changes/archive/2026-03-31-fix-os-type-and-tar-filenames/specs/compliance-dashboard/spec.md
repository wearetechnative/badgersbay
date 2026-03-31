## MODIFIED Requirements

### Requirement: Display OS type information

The system SHALL display OS type for each system when available, updating immediately upon report upload.

#### Scenario: OS type from neofetch data
- **WHEN** client uploads neofetch with `{"os": "NixOS 24.05"}` in JSON
- **THEN** dashboard displays "NixOS 24.05" in OS Type column

#### Scenario: OS type updates without server restart
- **WHEN** client uploads new neofetch report with different OS version
- **THEN** dashboard refresh shows updated OS type immediately

#### Scenario: Unknown OS type
- **WHEN** client uploads without neofetch report or OS information
- **THEN** dashboard displays "unknown" for OS type

#### Scenario: Dashboard refresh retrieves latest OS type
- **WHEN** user clicks refresh button or auto-refresh triggers
- **THEN** dashboard shows current OS type from cache without requiring server restart

## ADDED Requirements

### Requirement: Display tar archive download links

The system SHALL provide download links for tar archives with recognizable filenames.

#### Scenario: Tar badge links to most recent tar
- **WHEN** system has uploaded tar archive(s)
- **THEN** dashboard TAR badge links to most recently uploaded tar file

#### Scenario: Downloaded tar has meaningful filename
- **WHEN** user clicks TAR badge for system "lobos-wtoorren" with file `honeybadger-20260330-142931.tar.gz`
- **THEN** browser downloads as `lobos-wtoorren-honeybadger-20260330-142931.tar.gz`

#### Scenario: Tar badge handles both naming conventions
- **WHEN** system directory contains both `submission-*` and `honeybadger-*` tar files
- **THEN** dashboard links to most recent by modification time
