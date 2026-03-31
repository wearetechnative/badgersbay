# Bugfixes

This document tracks bug fixes applied to the Honeybadger Server.

## 2026-03-17: Vulnix Array Validation Bug

**Severity:** High
**Component:** Report Ingestion (validation)
**Affected versions:** All versions before this fix

### Problem

The validation logic in `validate_report_structure()` (honeybadger_server.py:338) had a two-step validation:

1. **Line 340-341:** Generic check requiring ALL reports to be JSON objects (dict)
2. **Line 360-363:** Vulnix-specific check allowing dict OR array

The generic check failed before reaching the vulnix-specific validation, rejecting valid vulnix reports that were JSON arrays.

**Error message received:**
```
HTTP 400: Report data must be a JSON object
```

**Root cause:**
Vulnix reports from NixOS systems are typically JSON arrays of vulnerability objects:
```json
[
  {
    "name": "package-name",
    "version": "1.0",
    "affected_by": ["CVE-2024-XXXXX"],
    ...
  },
  ...
]
```

This format is valid per the spec (`openspec/specs/report-ingestion/spec.md:83-90`), but the implementation incorrectly rejected it.

### Solution

**File:** `honeybadger_server.py`
**Function:** `validate_report_structure()` (line 338-374)
**Changes:**

1. Removed the generic `isinstance(data, dict)` check that applied to all report types
2. Added type-specific validation for each report type:
   - **Lynis:** Must be dict
   - **Trivy:** Must be dict
   - **Vulnix:** Can be dict OR array ✓
   - **Neofetch:** Must be dict

**Diff summary:**
```python
# BEFORE (buggy)
def validate_report_structure(self, report_type, data):
    if not isinstance(data, dict):  # ❌ Blocks vulnix arrays
        return False, "Report data must be a JSON object"
    # ... type-specific checks never reached for arrays

# AFTER (fixed)
def validate_report_structure(self, report_type, data):
    report_type_lower = report_type.lower()

    if report_type_lower == 'lynis':
        if not isinstance(data, dict):  # ✓ Type-specific
            return False, "Invalid Lynis report: must be a JSON object"
    # ... each type has its own validation
    elif report_type_lower == 'vulnix':
        if not isinstance(data, (dict, list)):  # ✓ Now reachable!
            return False, "Invalid Vulnix report: must be a JSON object or array"
```

### Verification

**Test case:**
```bash
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  -H "X-OS-Type: nixos" \
  -H "X-Report-Type: vulnix" \
  -d @vulnix-client.json
```

**Expected result:**
```json
{
  "status": "success",
  "message": "Report saved successfully",
  "path": "reports/2026-03/testhost-testuser/vulnix-report.json",
  "audit_period": "2026-03",
  "sid": "testhost",
  "os_type": "nixos"
}
```

**Verified:** ✅ 2026-03-17 - Successfully uploaded 734KB vulnix array report

### Impact

- **Affected systems:** NixOS hosts using vulnix scanner
- **Backwards compatibility:** No breaking changes - only fixes previously broken functionality
- **Performance:** No impact
- **Security:** No security implications

### Related Documentation

- Spec: `openspec/specs/report-ingestion/spec.md` (lines 83-90) - Already correctly specified array support
- Implementation: `honeybadger_server.py:338-374`
- Test data: `vulnix-client.json` (734KB sample report)

### Deployment Notes

**Server restart required:** Yes (Python file modified)

**Migration needed:** No - this is a pure bugfix

**Client changes needed:** No - clients were always correct, server was rejecting valid data

---

## 2026-03-17: Remove SID from Storage Structure (Breaking Change)

**Severity:** Medium (breaking change, but early in compliance mode rollout)
**Component:** Report Storage, Compliance Tracking
**Affected versions:** Compliance mode enabled systems

### Problem

The compliance tracking feature extracted SID (System ID) from neofetch's `host` field to identify systems. However, the `host` field contains hardware model names (e.g., "LENOVO 21K9CTO1WW ") instead of stable system identifiers, causing:

1. **Directories with spaces:** `LENOVO 21K9CTO1WW -wtoorren/`
2. **Inconsistent tracking:** Same system creates multiple directories
3. **Confusing dashboard:** SID column shows hardware models, not meaningful identifiers

### Solution

**Removed SID entirely** and use hostname-username as the canonical identifier:
- Storage paths: `YYYY-MM/{hostname}-{username}/`
- API responses: No `sid` field
- Dashboards: "Hostname" column instead of "SID"
- Cache structure: Keys based on hostname-username

### Migration Procedure

#### 1. Identify Affected Directories

```bash
# Find directories with spaces (hardware model names)
find reports/ -name "* *" -type d
```

#### 2. Manual Migration (if needed)

For each incorrectly-named directory:

```bash
# Example: Move reports from hardware-model directory to hostname directory
SOURCE_DIR="reports/2026-03/LENOVO 21K9CTO1WW -wtoorren"
TARGET_DIR="reports/2026-03/lobos-wtoorren"

# Ensure target exists
mkdir -p "$TARGET_DIR"

# Move reports
mv "$SOURCE_DIR"/*.json "$TARGET_DIR/" 2>/dev/null || true

# Remove empty source directory
rmdir "$SOURCE_DIR" 2>/dev/null || true
```

**Note:** If target directory already exists with reports, the move will overwrite. Review manually if both directories have reports.

#### 3. Deployment

```bash
# Stop server
pkill -f honeybadger_server.py

# Deploy new code
# (copy updated honeybadger_server.py)

# Start server (cache rebuilds automatically)
python3 honeybadger_server.py &
```

### Breaking Changes

1. **Storage paths changed:**
   - Before: `2026-03/{sid}-{username}/`
   - After: `2026-03/{hostname}-{username}/`

2. **API response changed:**
   - Before: `{"status": "success", "sid": "...", ...}`
   - After: `{"status": "success", ...}` (no sid field)

3. **Dashboard changed:**
   - Before: "SID" column showing hardware model
   - After: "Hostname" column showing actual hostname

### Verification

**After deployment:**

1. Upload a report:
```bash
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "X-Hostname: webserver01" \
  -H "X-Username: admin" \
  -H "X-OS-Type: ubuntu" \
  -H "X-Report-Type: lynis" \
  -d @lynis-report.json
```

2. Verify response has no `sid` field:
```json
{
  "status": "success",
  "message": "Report saved successfully",
  "path": "reports/2026-03/webserver01-admin/lynis-report.json",
  "audit_period": "2026-03",
  "os_type": "ubuntu"
}
```

3. Verify directory structure:
```bash
ls reports/2026-03/
# Should show: webserver01-admin/ (hostname-username)
```

4. Check dashboard has no SID references:
```bash
curl -s http://localhost:7123/ | grep -i "SID"
# Should return empty (no SID found)
```

### Impact

- **Affected systems:** All systems using compliance mode
- **Backwards compatibility:** Breaking change for API consumers and storage structure
- **Client changes needed:** None (clients continue sending same headers)
- **Dashboard:** Hostname displayed instead of hardware model (improvement)

### Files Changed

- `honeybadger_server.py`:
  - ComplianceCache class (keys, fields)
  - save_report() - removed SID extraction
  - do_POST() - removed SID from response
  - generate_compliance_dashboard_html() - Hostname column
  - generate_status_html() - removed SID column
  - get_reports_status() - removed SID extraction

### Rollback

If issues occur, revert to previous code version. Directories created with new structure will remain (manual cleanup if needed).

---

## 2026-03-30: OS Type Not Updating on Dashboard Refresh

**Severity:** Medium
**Component:** Report Ingestion, Compliance Dashboard
**Affected versions:** Compliance mode enabled systems

### Problem

The OS Type column in the compliance dashboard was not updating when new reports arrived. The OS type would only refresh after restarting the server, causing confusion for users monitoring system status.

**Root cause:**
1. OS type was only extracted from X-OS-Type header during upload
2. Many clients didn't set this header, defaulting to "unknown"
3. The neofetch JSON payload contains the authoritative OS information in the `os` field
4. Cache rebuild at server start read from neofetch files directly, showing correct OS
5. New uploads only used header, overwriting correct cached OS type with "unknown"

**User impact:**
- Dashboard showed "unknown" for OS Type even though neofetch data contained correct information
- Required server restart to see correct OS type
- Inconsistent display between server restarts

### Solution

**Extract OS type directly from neofetch JSON payload when available:**

1. Check if report_type is "neofetch"
2. Extract `os` field from JSON data
3. Use extracted value as os_type (takes precedence over X-OS-Type header)
4. Pass to cache update so dashboard reflects immediately

**Priority order:**
- Neofetch JSON `os` field (most authoritative)
- X-OS-Type header (fallback)
- "unknown" (default)

### Implementation

**File:** `honeybadger_server.py`
**Function:** `do_POST()` (around line 876-882)

```python
# Extract OS type (will be used in compliance mode)
os_type = self.headers.get('X-OS-Type', 'unknown')

# If this is a neofetch report, extract OS type from the data itself
if report_type.lower() == 'neofetch' and isinstance(data, dict) and 'os' in data:
    os_type = data.get('os', os_type)
    logger.info(f"Extracted OS type from neofetch data: {os_type}")

# Save the report
saved_path, audit_period = self.save_report(hostname, username, report_type, data, os_type)
```

### Verification

**Test case:**
```bash
# Upload neofetch without X-OS-Type header
curl -X POST http://localhost:7123/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  -H "X-Report-Type: neofetch" \
  -d '{"os": "NixOS 24.05", "hostname": "testhost", "kernel": "6.1.0"}'
```

**Expected result:**
1. Server logs: `Extracted OS type from neofetch data: NixOS 24.05`
2. Dashboard refresh shows "NixOS 24.05" in OS Type column immediately
3. No server restart required

### Impact

- **Affected systems:** All systems using compliance mode
- **Backwards compatibility:** Fully backward compatible (X-OS-Type header still supported)
- **Client changes needed:** None (improvement for all clients)
- **API changes:** None (response format unchanged)
- **Dashboard:** OS Type column now updates immediately on refresh

---

## 2026-03-30: Tar Archive Filename Prefix

**Severity:** Low (usability improvement)
**Component:** Report Storage
**Affected versions:** All versions with tar submission support

### Problem

When users uploaded tar archives via `/submit-tar`, the server renamed files with a generic "submission-" prefix:
- Upload: `honeybadger-lobos-wtoorren-30-03-2026.tar.gz`
- Stored as: `submission-20260330-142931.tar.gz`
- Downloaded as: `lobos-wtoorren-submission-20260330-142931.tar.gz`

This made downloaded files harder to identify as Honeybadger reports.

### Solution

Changed tar filename prefix from "submission-" to "honeybadger-" to match user expectations and maintain recognizable naming convention.

### Implementation

**File:** `honeybadger_server.py`
**Function:** `do_POST_submit_tar()` (around line 970)

**Change:**
```python
# BEFORE
tar_filename = f"submission-{timestamp}.tar.gz"

# AFTER
tar_filename = f"honeybadger-{timestamp}.tar.gz"
```

### Verification

**Test case:**
```bash
# Upload tar archive
curl -X POST http://localhost:7123/submit-tar \
  -H "Authorization: Bearer $TOKEN" \
  -H "X-Hostname: testhost" \
  -H "X-Username: testuser" \
  --data-binary @reports.tar.gz
```

**Expected result:**
- Server logs: `Tar file saved: reports/2026-03/testhost-testuser/honeybadger-20260330-142931.tar.gz`
- Download filename: `testhost-testuser-honeybadger-20260330-142931.tar.gz`

### Impact

- **Backwards compatibility:** Existing "submission-*" files remain accessible and downloadable
- **Client changes needed:** None
- **API changes:** None (server-internal naming only)
- **Dashboard:** TAR badge continues to work with both naming conventions
