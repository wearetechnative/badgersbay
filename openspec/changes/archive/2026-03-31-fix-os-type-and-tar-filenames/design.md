## Context

Currently, the OS type in the compliance dashboard is only updated during:
1. Initial cache rebuild at server startup (reads from neofetch-report.json files)
2. New uploads where X-OS-Type header is provided

The problem occurs when:
- User uploads neofetch report with OS information in the JSON payload
- Cache receives update with only X-OS-Type header (often set to 'unknown')
- Cached OS type becomes 'unknown' despite neofetch file containing correct data
- Dashboard shows 'unknown' until server restart forces cache rebuild from files

Additionally, tar archives are saved with `submission-{timestamp}.tar.gz` naming, but users expect filenames starting with `honeybadger-` to match their upload naming conventions.

## Goals / Non-Goals

**Goals:**
- Always extract OS type from neofetch JSON data when available during upload
- Update tar archive naming to use `honeybadger-` prefix for consistency
- Ensure dashboard shows correct OS type without requiring server restart
- Maintain backward compatibility with existing X-OS-Type header
- Preserve simple, single-file architecture

**Non-Goals:**
- Retroactively fix OS type for existing stored reports (manual server restart handles this)
- Add new API endpoints or change request/response formats
- Modify neofetch report structure or validation rules
- Add database or persistent cache storage

## Decisions

### Decision 1: Priority order for OS type extraction

**Choice:** Check neofetch JSON data first, fall back to X-OS-Type header

**Rationale:**
- Neofetch JSON is authoritative source (generated directly by neofetch tool)
- X-OS-Type header is convenience mechanism but often defaults to 'unknown'
- Client scripts may not properly set X-OS-Type, but neofetch JSON is always correct

**Alternatives considered:**
- Header-only approach: Rejected because many clients don't set this correctly
- Dual storage: Rejected as over-engineering for simple bug fix

**Implementation:**
```python
# In do_POST(), after report validation:
os_type = self.headers.get('X-OS-Type', 'unknown')

if report_type.lower() == 'neofetch' and isinstance(data, dict):
    os_type = data.get('os', os_type)  # Prefer JSON over header
```

### Decision 2: Tar filename format change

**Choice:** Use `honeybadger-{timestamp}.tar.gz` instead of `submission-{timestamp}.tar.gz`

**Rationale:**
- Matches user expectations and upload naming conventions
- Makes downloaded files immediately recognizable as honeybadger reports
- Maintains timestamp uniqueness for multiple uploads per day
- No risk of collision with existing files (timestamp ensures uniqueness)

**Alternatives considered:**
- Preserve original filename completely: Rejected due to security concerns (path traversal)
- Use hostname in filename: Rejected as timestamp already provides uniqueness

**Implementation:**
```python
# In do_POST_submit_tar():
tar_filename = f"honeybadger-{timestamp}.tar.gz"  # was: submission-{timestamp}
```

### Decision 3: Cache update behavior

**Choice:** Pass extracted OS type to cache.update_system() call

**Rationale:**
- Cache already accepts os_type parameter in update_system()
- No structural changes needed to ComplianceCache class
- Update happens in same code path as file write (atomic from user perspective)

**Implementation:**
```python
# In do_POST(), after extracting os_type:
if self.config.compliance_enabled and self.compliance_cache:
    self.compliance_cache.update_system(
        audit_period, hostname, username, report_type.lower(), os_type
    )
```

## Risks / Trade-offs

**Risk:** Neofetch JSON structure changes in future versions
→ **Mitigation:** Code already uses `.get('os', fallback)` pattern; missing field falls back to header value gracefully

**Risk:** Existing clients rely on `submission-` prefix for automation
→ **Mitigation:** Extremely unlikely (prefix is server-internal detail); download filename also includes directory name for identification. Existing `submission-*` files continue to work.

**Risk:** OS type extraction happens after validation but could fail
→ **Mitigation:** JSON is already validated at this point; use defensive `.get()` with fallback

**Trade-off:** Small performance overhead checking report_type and data structure
→ **Acceptable:** Single string comparison and dict check; negligible cost vs correctness benefit

## Migration Plan

**Deployment:**
1. Apply code changes to single Python file
2. Restart server (triggers cache rebuild with new logic)
3. No configuration changes needed
4. No database migrations (file-based storage)

**Validation:**
1. Upload neofetch report via POST /
2. Verify dashboard shows correct OS type immediately (no restart needed)
3. Upload tar archive via POST /submit-tar
4. Download archive and verify filename starts with `honeybadger-`

**Rollback:**
- Revert single Python file
- Restart server
- No data cleanup needed (files remain compatible)

**Testing strategy:**
- Use existing test scripts (`test.sh`, `test-tar-submit.sh`)
- Verify neofetch reports with various OS values
- Confirm tar downloads have correct filename prefix
