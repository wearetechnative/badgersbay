## MODIFIED Requirements

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

### Requirement: Display system compliance table

The system SHALL display a table showing compliance status for each system in the audit period.

Columns:
- SID (system identifier from neofetch)
- Username
- OS Type
- Upload Date (latest upload in period)
- Reports (badges: N L T V)
- Status (Complete/Incomplete with details)

#### Scenario: Complete system row
- **WHEN** laptop-SN001 has complete set in 2026-03
- **THEN** row shows: "laptop-SN001 | alice | ubuntu | 2026-03-15 | N L T | ✓ Complete"

#### Scenario: Incomplete system row
- **WHEN** laptop-SN002 missing trivy/vulnix in 2026-03
- **THEN** row shows: "laptop-SN002 | bob | nixos | 2026-03-10 | N L | ⚠ Missing: T or V"

### Requirement: Period navigation

The system SHALL allow users to navigate between different audit periods.

#### Scenario: Period dropdown
- **WHEN** user clicks period selector
- **THEN** dropdown shows all available audit periods in reverse chronological order

#### Scenario: Switch period
- **WHEN** user selects different period from dropdown
- **THEN** dashboard refreshes to show data for selected period

## REMOVED Requirements

### Requirement: Timestamp color coding

**Reason**: Replaced by compliance-based status indicators. In compliance mode, status is based on report completeness, not recency.

**Migration**: Compliance dashboard uses completion status (Complete/Incomplete) instead of time-based colors.

### Requirement: Auto-refresh every 30 seconds

**Reason**: For compliance tracking, real-time updates are less critical. Manual refresh is sufficient.

**Migration**: Users can manually refresh browser. Future enhancement could add configurable auto-refresh.

## ADDED Requirements

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
