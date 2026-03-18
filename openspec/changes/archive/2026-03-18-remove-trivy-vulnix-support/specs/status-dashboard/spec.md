## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Trivy and Vulnix status logic
**Reason**: Trivy and Vulnix report types are no longer supported for ISO compliance use case
**Migration**: Systems that previously required Trivy or Vulnix will now be marked OK with only Neofetch + Lynis. Update client scripts to stop submitting Trivy/Vulnix reports.

### Requirement: Trivy statistics card
**Reason**: Trivy report type is no longer supported
**Migration**: Remove from dashboard display. Historical data remains on disk but won't be counted.

### Requirement: Vulnix statistics card
**Reason**: Vulnix report type is no longer supported
**Migration**: Remove from dashboard display. Historical data remains on disk but won't be counted.

### Requirement: Trivy report badge
**Reason**: Trivy report type is no longer supported
**Migration**: Badge will not appear in dashboard even if file exists on disk.

### Requirement: Vulnix report badge
**Reason**: Vulnix report type is no longer supported
**Migration**: Badge will not appear in dashboard even if file exists on disk.
