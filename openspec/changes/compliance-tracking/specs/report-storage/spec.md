## MODIFIED Requirements

### Requirement: Directory structure based on audit periods

The system SHALL store reports in directories organized by audit period instead of individual upload dates when compliance mode is enabled.

**Directory Format (compliance enabled):** `{YYYY-MM}/`

Where:
- `YYYY-MM`: Audit period (year and audit month)
- Within each period: `{hostname}-{username}/` subdirectories

**Directory Format (legacy mode):** `{hostname}-{username}-{YYYYMMDD}/`

#### Scenario: Compliance mode storage structure
- **WHEN** compliance.enabled is true
- **THEN** reports stored in `./reports/2026-03/laptop-SN001-alice/`

#### Scenario: Legacy mode storage structure
- **WHEN** compliance.enabled is false or not configured
- **THEN** reports stored in `./reports/laptop-SN001-alice-20260316/`

#### Scenario: System directory within audit period
- **WHEN** laptop-SN001 (user alice) uploads to audit period 2026-03
- **THEN** reports stored in `./reports/2026-03/laptop-SN001-alice/neofetch-report.json`

#### Scenario: Upload date mapping
- **WHEN** upload received on 2026-04-15 with audit_months [3, 9]
- **THEN** stored in `./reports/2026-09/` (next audit period)

### Requirement: Overwrite behavior in audit periods

The system SHALL overwrite reports when same system uploads multiple times to the same audit period.

#### Scenario: Multiple uploads same audit period
- **WHEN** laptop-SN001 uploads on 2026-02-10 and 2026-03-15 (both map to 2026-03)
- **THEN** second upload overwrites first in `./reports/2026-03/laptop-SN001-alice/`

#### Scenario: Different audit periods preserved
- **WHEN** laptop-SN001 uploads to 2026-03 period and later to 2026-09 period
- **THEN** both audit period directories contain separate reports for same system

### Requirement: System identification

The system SHALL identify unique systems by SID (from neofetch) rather than hostname.

#### Scenario: Extract SID from neofetch
- **WHEN** neofetch-report.json contains `{"host": "laptop-SN001"}`
- **THEN** system is identified by SID "laptop-SN001"

#### Scenario: User changes for same system
- **WHEN** laptop-SN001 uploads with user "alice" then later with user "bob"
- **THEN** creates separate directories: `laptop-SN001-alice/` and `laptop-SN001-bob/`

### Requirement: Path structure includes SID

The system SHALL use SID in directory names for better system identification.

#### Scenario: Directory naming with SID
- **WHEN** system with SID "laptop-SN001" (hostname "alice-laptop") uploads as user "alice"
- **THEN** directory created as `laptop-SN001-alice/` (using SID, not hostname)

## ADDED Requirements

### Requirement: Store OS type metadata

The system SHALL store OS type metadata when provided by client.

#### Scenario: OS type from X-OS-Type header
- **WHEN** client uploads with header `X-OS-Type: nixos`
- **THEN** system stores os_type metadata associated with the system

#### Scenario: Missing OS type header
- **WHEN** client uploads without X-OS-Type header
- **THEN** system stores os_type as "unknown"
