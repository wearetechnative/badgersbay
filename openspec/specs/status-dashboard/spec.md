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

Columns:

| Column | Source | Description |
|--------|--------|-------------|
| **Hostname** | Directory name parse | System hostname |
| **SID** | `neofetch-report.json → host` field | System identifier (short hostname) |
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

- Searches across: hostname, SID, username, date
- Case-insensitive
- Instant update (no page reload)
- Shows "No results" message when no matches

### Auto-Refresh

Page automatically reloads every 30 seconds to show latest data.

## Technical Details

### Report Discovery

Dashboard scans `storage_location` directory:

1. Iterate all subdirectories
2. Parse directory name: `<hostname>-<username>-<yyyymmdd>`
3. Check for existence of each report type
4. Extract SID from neofetch report's `host` field
5. Find latest mtime across all JSON files
6. Sort by last update (newest first)

### SID Extraction

**Source:** `neofetch-report.json`

**Fields checked (in order):**
1. `host` (preferred - short hostname)
2. `hostname` (fallback - FQDN)

**Display:** `-` if neofetch missing or field not found

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
