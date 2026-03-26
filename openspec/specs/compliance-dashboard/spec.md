## MODIFIED Requirements

### Requirement: Display compliance by audit period

The system SHALL display a dashboard view organized by audit period showing compliance status for all systems.

#### Scenario: Select audit period
- **WHEN** user accesses dashboard
- **THEN** system displays dropdown/tabs to select audit period (e.g., "2026-03", "2026-09")

#### Scenario: View period summary
- **WHEN** user selects audit period "2026-03"
- **THEN** system displays summary: total systems uploaded, complete count, incomplete count

#### Scenario: List systems in period
- **WHEN** viewing audit period
- **THEN** system displays table with columns: Hostname, Username, OS Type, Upload Date, Reports, Status

#### Scenario: No SID column displayed
- **WHEN** viewing compliance dashboard
- **THEN** table does NOT include SID column (uses Hostname instead)

### Requirement: Maintain report download functionality

The system SHALL continue to support downloading individual reports from the compliance dashboard using hostname-based paths.

#### Scenario: Download complete report
- **WHEN** user clicks on report badge (e.g., "L" for Lynis)
- **THEN** system downloads the corresponding JSON file

#### Scenario: Download URL format
- **WHEN** downloading lynis report for webserver01-admin from 2026-03 period
- **THEN** URL is `/reports/2026-03/webserver01-admin/lynis-report.json`

#### Scenario: Download filename format
- **WHEN** downloading lynis report for webserver01-admin from 2026-03 period
- **THEN** browser suggests filename "lynis-report.json" or "2026-03-webserver01-admin-lynis-report.json"
