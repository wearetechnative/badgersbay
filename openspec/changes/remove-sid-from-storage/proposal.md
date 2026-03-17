## Why

The current SID (System ID) extraction from neofetch's `host` field causes storage path issues. The `host` field contains hardware model names with spaces (e.g., "LENOVO 21K9CTO1WW "), creating directories like `LENOVO 21K9CTO1WW -wtoorren/` instead of the expected `lobos-wtoorren/`. This breaks the storage contract and causes new uploads to be placed in the wrong folder, preventing systems from being properly tracked.

## What Changes

- Remove SID extraction logic from save_report() function
- Use only hostname-username for compliance mode directory naming
- Simplify ComplianceCache to track by hostname-username instead of sid-username
- Remove SID field from dashboard displays (both compliance and legacy)
- Remove SID from API responses
- Clean up neofetch parsing logic that attempts to read SID from existing reports

## Capabilities

### New Capabilities
<!-- None - this is a simplification change -->

### Modified Capabilities
- `report-storage`: Directory naming changes from `{sid}-{username}` to `{hostname}-{username}` in compliance mode
- `report-ingestion`: Remove SID extraction and SID from response payload
- `compliance-dashboard`: Remove SID column and references, display hostname instead
- `status-dashboard`: Remove SID field from legacy dashboard

## Impact

**Storage Structure:**
- Compliance mode paths change from `YYYY-MM/{sid}-{username}/` to `YYYY-MM/{hostname}-{username}/`
- Existing incorrectly-named directories (with spaces) will be orphaned
- New uploads will use correct hostname-based paths
- Legacy mode (date-based) storage is unaffected

**Breaking Changes:**
- **BREAKING**: Storage path structure changes in compliance mode
- **BREAKING**: API response no longer includes `sid` field
- **BREAKING**: Dashboard no longer displays SID column

**Code Affected:**
- `ComplianceCache` class: key structure and update logic
- `save_report()`: remove SID extraction and fallback logic
- `do_POST()`: remove SID from response
- `generate_compliance_dashboard_html()`: remove SID column
- `generate_status_html()`: remove SID field

**Migration:**
- Manual cleanup needed for existing directories with spaces/incorrect names
- No automatic migration provided (consistent with existing approach)
