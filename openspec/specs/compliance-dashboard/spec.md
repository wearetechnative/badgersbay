# Compliance Dashboard

## Purpose
Defines what the compliance dashboard shows per system: the operating system
reported by the client, and links to the stored evidence for that system.

## Requirements

### Requirement: Display OS type information

The system SHALL display OS type for each system, read from the stored
fastfetch report, updating immediately upon report upload.

#### Scenario: OS type from neofetch data
- **WHEN** a system directory contains `neofetch-report.json` from an earlier
  client generation and no `fastfetch-report.json`
- **THEN** the dashboard displays "unknown" and does not read the legacy file
  as system information

#### Scenario: OS type from fastfetch data
- **WHEN** a client uploads fastfetch data with `{"os": "NixOS 26.05 (Yarara)"}`
- **THEN** the dashboard displays "NixOS 26.05 (Yarara)" in the OS Type column

#### Scenario: OS type updates without server restart
- **WHEN** a client uploads a new fastfetch report with a different OS version
- **THEN** a dashboard refresh shows the updated OS type

#### Scenario: OS type from tar submission header
- **WHEN** a client submits a tar archive that carries no fastfetch member but
  does send an `X-OS-Type` header
- **THEN** the dashboard displays that value; the header is now a fallback,
  because an archive containing fastfetch data is read directly

#### Scenario: Unknown OS type
- **WHEN** a system has no fastfetch report, or one without an `os` field
- **THEN** the dashboard displays "unknown" for OS type

#### Scenario: Dashboard refresh retrieves latest OS type
- **WHEN** a user clicks refresh or auto-refresh triggers
- **THEN** the dashboard shows the current OS type from the cache without
  requiring a server restart


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

### Requirement: Dashboard view organized by audit period

The system SHALL display the dashboard organized by audit period when compliance mode is enabled, replacing the chronological date-based view.

#### Scenario: Compliance mode dashboard structure
- **WHEN** compliance.enabled is true and user accesses dashboard
- **THEN** dashboard shows audit period selector and period-based compliance view

#### Scenario: Legacy mode dashboard structure
- **WHEN** compliance.enabled is false or not configured
- **THEN** dashboard shows traditional chronological listing by upload date

#### Scenario: Period selection
- **WHEN** user selects audit period "2026-03" from dropdown
- **THEN** dashboard displays all systems with uploads in that period

### Requirement: Display compliance summary statistics

The system SHALL display summary statistics for the selected audit period at the top of the dashboard.

#### Scenario: Summary statistics displayed
- **WHEN** viewing audit period dashboard
- **THEN** displays: total systems, complete count, incomplete count, compliance percentage

#### Scenario: Example summary
- **WHEN** period has 42 systems total, 38 complete, 4 incomplete
- **THEN** shows "Total: 42 | Complete: 38 (90%) | Incomplete: 4 (10%)"

### Requirement: Display system compliance table in compliance mode

The system SHALL display a table showing compliance status for each system in the audit period using hostname instead of SID.

**Columns:**
- Hostname (from X-Hostname header)
- Username
- OS Type
- Upload Date (latest upload in period)
- Reports (badges: F L)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row in compliance mode
- **WHEN** webserver01 has a complete set in 2026-09
- **THEN** row shows: "webserver01 | admin | ubuntu | 2026-09-15 | F L | ✓ Complete"

#### Scenario: Incomplete system row in compliance mode
- **WHEN** dbserver02 is missing lynis in 2026-09
- **THEN** row shows: "dbserver02 | dbadmin | nixos | 2026-09-10 | F | ⚠ Missing: lynis"

#### Scenario: No SID column
- **WHEN** viewing the compliance dashboard table
- **THEN** the table does NOT include a SID column; Hostname is the first column

### Requirement: Period navigation

The system SHALL allow users to navigate between different audit periods.

#### Scenario: Period dropdown
- **WHEN** user clicks period selector
- **THEN** dropdown shows all available audit periods in reverse chronological order

#### Scenario: Switch period
- **WHEN** user selects different period from dropdown
- **THEN** dashboard refreshes to show data for selected period

### Requirement: Filter by compliance status

The system SHALL allow filtering systems by compliance status.

#### Scenario: Show all systems
- **WHEN** filter set to "All"
- **THEN** all systems in period are displayed

#### Scenario: Show only incomplete
- **WHEN** filter set to "Incomplete"
- **THEN** only systems with incomplete or missing reports are shown

#### Scenario: Show only complete
- **WHEN** filter set to "Complete"
- **THEN** only systems with complete report sets are shown

### Requirement: Report badge for fastfetch

The system SHALL render the system information report as badge `F` linking to
the stored `fastfetch-report.json`.

#### Scenario: Badge rendered for present report
- **WHEN** a system has `fastfetch-report.json` in the selected audit period
- **THEN** the Reports column shows badge `F` linking to that file

#### Scenario: Legend reflects current report types
- **WHEN** the dashboard renders its legend
- **THEN** it reads "F=Fastfetch, L=Lynis, TAR=Tar Archive"
