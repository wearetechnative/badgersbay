# Status Dashboard

## Purpose
Defines the legacy dashboard, served when `compliance.enabled` is false. It
lists report directories chronologically by upload date rather than by audit
period. Legacy mode is retained as a fallback: nothing runs on it, but it must
keep working so the server can be switched back if compliance mode fails. The
compliance-mode dashboard is specified in `compliance-dashboard`.

## Requirements

### Requirement: Statistics Cards

The dashboard SHALL display summary statistics for all reports.

| Metric | Description |
|--------|-------------|
| Unique host-user combinations | Count of distinct hostname-username pairs |
| Lynis reports | Total reports containing Lynis data |
| Neofetch reports | Total reports containing Neofetch data |

#### Scenario: Statistics calculation
- **WHEN** dashboard loads
- **THEN** it scans all report directories and displays:
  - Total unique host-user combinations
  - Count of directories containing `lynis-report.json`
  - Count of directories containing `neofetch-report.json`

### Requirement: Legacy dashboard display

The system SHALL display hostname and username in legacy mode without SID field.

#### Scenario: Legacy mode table structure
- **WHEN** compliance.enabled is false
- **THEN** table shows columns: Hostname, Username, Report Date, Reports, Last Update

#### Scenario: Legacy mode row display
- **WHEN** viewing legacy dashboard
- **THEN** row shows: "webserver01 | admin | 2026-03-16 | N L | 2026-03-16 14:23"

#### Scenario: No SID in legacy mode
- **WHEN** viewing legacy dashboard
- **THEN** table does NOT include SID field or column

### Requirement: Status Logic

A system SHALL be marked as **OK (Green)** when both required reports are present:
- Neofetch (required - provides system identity)
- Lynis (required - system hardening audit)

A system SHALL be marked as **NOK (Red)** when any required report is missing.

#### Scenario: OK status with complete reports
- **WHEN** a host directory contains both `neofetch-report.json` AND `lynis-report.json`
- **THEN** dashboard displays status as OK (green)

#### Scenario: NOK status missing Neofetch
- **WHEN** a host directory contains `lynis-report.json` but NOT `neofetch-report.json`
- **THEN** dashboard displays status as NOK (red)

#### Scenario: NOK status missing Lynis
- **WHEN** a host directory contains `neofetch-report.json` but NOT `lynis-report.json`
- **THEN** dashboard displays status as NOK (red)

#### Scenario: NOK status missing all reports
- **WHEN** a host directory exists but contains no report files
- **THEN** dashboard displays status as NOK (red)

### Requirement: Report Badges

The dashboard SHALL display badges for each available report type in the Reports column.

**Green badges** (report exists, clickable to download):
- `Lynis`
- `Neofetch`

**Red badge** (missing required report):
- `Missing Neofetch`

#### Scenario: Complete reports display
- **WHEN** a host directory contains both Lynis and Neofetch reports
- **THEN** dashboard displays two green badges: "Lynis" and "Neofetch"

#### Scenario: Missing Neofetch warning
- **WHEN** a host directory is missing `neofetch-report.json`
- **THEN** dashboard displays a red "Missing Neofetch" badge

#### Scenario: Download filename
- **WHEN** a user clicks a report badge
- **THEN** the file downloads as `<hostname>-<username>-<yyyymmdd>-<type>-report.json`

### Requirement: Search filtering

The legacy dashboard SHALL filter rows client-side from a search input, without
reloading the page.

#### Scenario: Match on any listed field
- **WHEN** a user types a term matching a hostname, username or date
- **THEN** only rows matching that term remain visible

#### Scenario: Case insensitive
- **WHEN** a user types "WEBSERVER" and a row has hostname "webserver01"
- **THEN** the row remains visible

#### Scenario: No matches
- **WHEN** no row matches the search term
- **THEN** the dashboard shows a "No results" message

#### Scenario: Clearing the search
- **WHEN** the search input is emptied
- **THEN** all rows become visible again

### Requirement: Auto-refresh in legacy mode only

The legacy dashboard SHALL reload itself every 30 seconds. The compliance
dashboard SHALL NOT auto-refresh; it offers a manual refresh control instead.

#### Scenario: Legacy mode reloads
- **WHEN** the legacy dashboard is open and 30 seconds pass
- **THEN** the page reloads to show current data

#### Scenario: Compliance mode does not reload
- **WHEN** the compliance dashboard is open
- **THEN** the page does not reload on a timer
