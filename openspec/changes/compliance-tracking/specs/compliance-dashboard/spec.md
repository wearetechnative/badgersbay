## ADDED Requirements

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
- **THEN** system displays table with columns: SID, Username, OS Type, Upload Date, Reports, Status

### Requirement: Show compliance status indicators

The system SHALL visually indicate compliance status for each system.

#### Scenario: Complete status display
- **WHEN** system has complete report set
- **THEN** status column shows green checkmark (✓) with text "Complete"

#### Scenario: Incomplete status display
- **WHEN** system has incomplete report set
- **THEN** status column shows warning icon (⚠) with text "Incomplete" and list of missing reports

#### Scenario: No reports status
- **WHEN** system has no reports for the period
- **THEN** status column shows red X (✗) with text "No reports"

### Requirement: Display report badges

The system SHALL show which reports are present for each system using badges.

#### Scenario: Available reports shown
- **WHEN** system has neofetch, lynis, and trivy
- **THEN** dashboard displays badges "N L T"

#### Scenario: Missing reports indicated
- **WHEN** system is missing trivy/vulnix
- **THEN** badge area shows "N L" without scanner badge

#### Scenario: Badge legend
- **WHEN** user views dashboard
- **THEN** legend explains N=Neofetch, L=Lynis, T=Trivy, V=Vulnix

### Requirement: Filter and search systems

The system SHALL allow filtering systems by compliance status.

#### Scenario: Show all systems
- **WHEN** filter is set to "All"
- **THEN** all systems in period are displayed

#### Scenario: Show only incomplete
- **WHEN** filter is set to "Incomplete"
- **THEN** only systems with incomplete or missing reports are displayed

#### Scenario: Show only complete
- **WHEN** filter is set to "Complete"
- **THEN** only systems with complete report sets are displayed

### Requirement: Navigate between periods

The system SHALL allow navigation between different audit periods.

#### Scenario: Switch to different period
- **WHEN** user selects different audit period from dropdown
- **THEN** dashboard refreshes to show data for selected period

#### Scenario: Show available periods
- **WHEN** user opens period selector
- **THEN** all audit periods with uploaded data are shown in reverse chronological order

### Requirement: Display OS type information

The system SHALL display OS type for each system when available.

#### Scenario: OS type from header
- **WHEN** client uploaded with X-OS-Type header
- **THEN** dashboard displays OS type in dedicated column

#### Scenario: Unknown OS type
- **WHEN** client uploaded without X-OS-Type header
- **THEN** dashboard displays "unknown" or "-" for OS type

### Requirement: Maintain report download functionality

The system SHALL continue to support downloading individual reports from the compliance dashboard.

#### Scenario: Download complete report
- **WHEN** user clicks on report badge (e.g., "L" for Lynis)
- **THEN** system downloads the corresponding JSON file

#### Scenario: Download filename format
- **WHEN** downloading lynis report for laptop-SN001 from 2026-03 period
- **THEN** filename is "2026-03-laptop-SN001-alice-lynis-report.json"
