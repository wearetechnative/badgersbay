## REMOVED Requirements

### Requirement: System identification

**Reason**: SID extraction from neofetch `host` field is unreliable - it contains hardware model names with spaces (e.g., "LENOVO 21K9CTO1WW ") rather than stable system identifiers. This causes filesystem path issues and inconsistent tracking.

**Migration**: Use hostname (from X-Hostname header) instead of SID for system identification. Directory names change from `{sid}-{username}` to `{hostname}-{username}`.

**Original requirement:**
The system SHALL identify unique systems by SID (from neofetch) rather than hostname.

### Requirement: Path structure includes SID

**Reason**: SID-based paths create directories with spaces and special characters, breaking the storage contract. Hostname-based paths are simpler and more reliable.

**Migration**:
1. Find affected directories: `find reports/ -name "* *" -type d`
2. Manually move reports to hostname-based directories
3. Remove orphaned directories

**Original requirement:**
The system SHALL use SID in directory names for better system identification.

## MODIFIED Requirements

### Requirement: Directory structure based on audit periods

The system SHALL store reports in directories organized by audit period instead of individual upload dates when compliance mode is enabled.

**Directory Format (compliance enabled):** `{YYYY-MM}/{hostname}-{username}/`

Where:
- `YYYY-MM`: Audit period (year and audit month)
- `hostname`: From X-Hostname header
- `username`: From X-Username header

**Directory Format (legacy mode):** `{hostname}-{username}-{YYYYMMDD}/`

#### Scenario: Compliance mode storage structure
- **WHEN** compliance.enabled is true
- **THEN** reports stored in `./reports/2026-03/webserver01-admin/`

#### Scenario: Legacy mode storage structure
- **WHEN** compliance.enabled is false or not configured
- **THEN** reports stored in `./reports/webserver01-admin-20260316/`

#### Scenario: System directory within audit period
- **WHEN** webserver01 (user admin) uploads to audit period 2026-03
- **THEN** reports stored in `./reports/2026-03/webserver01-admin/lynis-report.json`

#### Scenario: Upload date mapping
- **WHEN** upload received on 2026-04-15 with audit_months [3, 9]
- **THEN** stored in `./reports/2026-09/` (next audit period)

#### Scenario: User changes for same hostname
- **WHEN** webserver01 uploads with user "admin" then later with user "sysadmin"
- **THEN** creates separate directories: `webserver01-admin/` and `webserver01-sysadmin/`

### Requirement: Overwrite behavior in audit periods

The system SHALL overwrite reports when same hostname-username combination uploads multiple times to the same audit period.

#### Scenario: Multiple uploads same audit period
- **WHEN** webserver01-admin uploads on 2026-02-10 and 2026-03-15 (both map to 2026-03)
- **THEN** second upload overwrites first in `./reports/2026-03/webserver01-admin/`

#### Scenario: Different audit periods preserved
- **WHEN** webserver01-admin uploads to 2026-03 period and later to 2026-09 period
- **THEN** both audit period directories contain separate reports for same hostname-username

#### Scenario: Same hostname different users
- **WHEN** webserver01 uploads as "admin" and "sysadmin" in same period
- **THEN** separate directories: `webserver01-admin/` and `webserver01-sysadmin/`
