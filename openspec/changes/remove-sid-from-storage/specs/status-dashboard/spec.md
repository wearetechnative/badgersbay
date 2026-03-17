## MODIFIED Requirements

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
