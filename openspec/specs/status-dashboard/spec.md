# Status Dashboard

## Overview

Web-based HTML dashboard that displays all collected security reports with filtering, status indicators, and download capabilities.

## Access

```
GET /
GET /status
```

Both endpoints serve the same HTML dashboard.

## Dashboard Features

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

### Report Table

### Requirement: Display system compliance table

The system SHALL display a table showing compliance status for each system in the audit period using hostname instead of SID.

**Columns:**
- Hostname (from X-Hostname header)
- Username
- OS Type
- Upload Date (latest upload in period)
- Reports (badges: N L T V)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row
- **WHEN** webserver01 has complete set in 2026-03
- **THEN** row shows: "webserver01 | admin | ubuntu | 2026-03-15 | N L T | ✓ Complete"

#### Scenario: Incomplete system row
- **WHEN** dbserver02 missing trivy/vulnix in 2026-03
- **THEN** row shows: "dbserver02 | dbadmin | nixos | 2026-03-10 | N L | ⚠ Missing: T or V"

#### Scenario: No SID column
- **WHEN** viewing compliance dashboard table
- **THEN** table does NOT include SID column (uses Hostname as first column)

### Requirement: Legacy dashboard display

The system SHALL display hostname and username in legacy mode without SID field.

#### Scenario: Legacy mode table structure
- **WHEN** compliance.enabled is false
- **THEN** table shows columns: Hostname, Username, Report Date, Reports, Last Update

#### Scenario: Legacy mode row display
- **WHEN** viewing legacy dashboard
- **THEN** row shows: "webserver01 | admin | 2026-03-16 | N L T | 2026-03-16 14:23"

#### Scenario: No SID in legacy mode
- **WHEN** viewing legacy dashboard
- **THEN** table does NOT include SID field or column

### Legacy Mode Columns

| Column | Source | Description |
|--------|--------|-------------|
| **Hostname** | Directory name parse | System hostname |
| **Username** | Directory name parse | User who submitted reports |
| **Report Date** | Directory name (YYYYMMDD) | Date reports were submitted |
| **Last Update** | Latest file mtime in directory | Most recent report update timestamp |
| **Reports** | File existence checks | Badge links for each available report |
| **Status** | Validation logic | OK/NOK based on report combination |

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

### Timestamp Colors

| Color | Condition | Meaning |
|-------|-----------|---------|
| **Green** | Valid combination + <24h old | Recent and complete |
| **Red** | Invalid combination | Missing required reports |
| **Black** | Valid combination + ≥24h old | Complete but not recent |

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

Downloads are named: `<hostname>-<username>-<yyyymmdd>-<type>-report.json`

### Filtering

Real-time client-side filtering via search input:

- Searches across: hostname, username, date
- Case-insensitive
- Instant update (no page reload)
- Shows "No results" message when no matches

### Auto-Refresh

Page automatically reloads every 30 seconds to show latest data (legacy mode only).

## ADDED Requirements

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
- Reports (badges: N L T V)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row in compliance mode
- **WHEN** webserver01 has complete set in 2026-03
- **THEN** row shows: "webserver01 | admin | ubuntu | 2026-03-15 | N L T | ✓ Complete"

#### Scenario: Incomplete system row in compliance mode
- **WHEN** dbserver02 missing trivy/vulnix in 2026-03
- **THEN** row shows: "dbserver02 | dbadmin | nixos | 2026-03-10 | N L | ⚠ Missing: T or V"

### Requirement: Period navigation

The system SHALL allow users to navigate between different audit periods.

#### Scenario: Period dropdown
- **WHEN** user clicks period selector
- **THEN** dropdown shows all available audit periods in reverse chronological order

#### Scenario: Switch period
- **WHEN** user selects different period from dropdown
- **THEN** dashboard refreshes to show data for selected period

### Requirement: Display OS type column

The system SHALL display the OS type for each system when available.

#### Scenario: OS type displayed
- **WHEN** system uploaded with X-OS-Type header value "ubuntu"
- **THEN** OS Type column shows "ubuntu"

#### Scenario: Unknown OS type
- **WHEN** system uploaded without X-OS-Type header
- **THEN** OS Type column shows "unknown" or "-"

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

## REMOVED Requirements

### Requirement: Auto-refresh in compliance mode

**Reason**: For compliance tracking, real-time updates are less critical. Manual refresh is sufficient.

**Migration**: Users can manually refresh browser. Auto-refresh remains in legacy mode only.

## Technical Details

### Report Discovery

Dashboard scans `storage_location` directory:

1. Iterate all subdirectories (handles both compliance and legacy mode structures)
2. Parse directory name:
   - Legacy: `<hostname>-<username>-<yyyymmdd>`
   - Compliance: `<YYYY-MM>/<hostname>-<username>`
3. Check for existence of each report type
4. Find latest mtime across all JSON files
5. Sort by last update (newest first)

### Styling

- Responsive design (max-width: 1200px)
- Sticky table header
- Max height: 600px with scroll
- Hover effects on table rows
- Clean, modern CSS (no external frameworks)

## Implementation Location

- HTML generation: `honeybadger_server.py:generate_status_html()` (line 332)
- Report scanning: `get_reports_status()` (line 259)
- GET handler: `do_GET()` (line 723)

## User Experience

### Loading Time

Scales linearly with number of report directories:
- ~10ms per 100 directories (SSD)
- No pagination (all reports loaded)

### Browser Compatibility

- Modern browsers (Chrome, Firefox, Safari, Edge)
- JavaScript required for filtering and auto-refresh
- No external dependencies (self-contained HTML)

## Future Enhancements

- Pagination for large datasets
- Sort by column (hostname, date, status)
- Export to CSV/JSON
- Historical trend graphs
- Real-time updates (WebSocket/SSE)
- Dark mode
- Customizable auto-refresh interval
