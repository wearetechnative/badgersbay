## Context

The Honeybadger server currently supports four report types (Lynis, Trivy, Vulnix, Neofetch) with complex validation logic to handle different system types (traditional Linux, containers, NixOS). For ISO compliance purposes, only Lynis (system hardening) and Neofetch (system identification) are needed.

The codebase is a single Python file (`honeybadger_server.py`) with embedded validation, storage, and HTML generation. This change will simplify the validation logic, reduce code complexity, and focus the tool on its primary ISO compliance use case.

**Current state:**
- Four report types with type-specific validation
- Complex "OK" status logic: (Neofetch + Lynis + Trivy) OR (Neofetch + Lynis + Vulnix)
- Dashboard displays all four report types
- Health endpoint counts all four report types

**Constraints:**
- Must maintain single-file architecture
- Must not break existing storage format (backward compatible on disk)
- Must maintain HTTP API contract for remaining types (Lynis, Neofetch)

## Goals / Non-Goals

**Goals:**
- Remove Trivy and Vulnix from accepted report types
- Simplify validation logic to only handle Lynis and Neofetch
- Update "OK" status logic to only require Neofetch + Lynis
- Update dashboard to only display Lynis and Neofetch reports
- Update health endpoint statistics to only count Lynis and Neofetch
- Maintain existing storage structure (files remain on disk, just not processed)

**Non-Goals:**
- Delete existing Trivy/Vulnix report files from disk (data preservation)
- Add new report types
- Change storage directory structure
- Add database backend
- Modify authentication or rate limiting

## Decisions

### Decision 1: Reject Trivy/Vulnix submissions vs. Accept-but-ignore

**Chosen approach:** Reject with HTTP 400 error

**Rationale:**
- Fail-fast feedback to clients that reports are no longer accepted
- Prevents clients from believing their reports are being processed
- Clear migration signal to update client scripts
- Maintains existing validation pattern (fail early)

**Alternative considered:** Accept reports but don't store/display them
- **Rejected because:** Silent failure is confusing for clients; wastes server resources

### Decision 2: Remove validation code vs. Keep but disable

**Chosen approach:** Remove validation code entirely

**Rationale:**
- Reduces code complexity and maintenance burden
- No need to maintain unused validation logic
- Clear signal that support is fully removed
- Simpler codebase for ISO compliance focus

**Alternative considered:** Keep validation code but gate it with config flag
- **Rejected because:** Adds unnecessary complexity; no planned re-enablement

### Decision 3: Handle existing Trivy/Vulnix files on disk

**Chosen approach:** Leave on disk, don't display in dashboard

**Rationale:**
- Data preservation (don't delete historical data)
- No risk of accidental data loss
- Allows manual recovery if needed
- Simpler implementation (no file deletion logic)

**Alternative considered:** Delete existing Trivy/Vulnix files as part of migration
- **Rejected because:** Risk of data loss; no compelling benefit

### Decision 4: Update "OK" status logic

**Chosen approach:** OK = Neofetch + Lynis (both required)

**Rationale:**
- Simplifies logic from complex OR conditions
- Aligns with ISO compliance requirements
- Clear requirements: identity (Neofetch) + hardening audit (Lynis)

**Previous logic:** (Neofetch + Lynis + Trivy) OR (Neofetch + Lynis + Vulnix)
**New logic:** Neofetch + Lynis

## Implementation Approach

### Phase 1: Validation Layer
- Update `valid_types` list to only include `['lynis', 'neofetch']`
- Remove Trivy validation logic from `validate_report_structure()`
- Remove Vulnix validation logic from `validate_report_structure()`
- Update error messages to only list supported types

### Phase 2: Storage Layer
- Update `save_report()` filename mapping to only handle lynis/neofetch
- Remove Trivy/Vulnix branches (will never be reached due to validation)

### Phase 3: Dashboard Layer
- Update `get_reports_status()` to only check for lynis/neofetch files
- Update status logic to: `is_ok = has_neofetch and has_lynis`
- Remove Trivy/Vulnix from statistics cards
- Remove Trivy/Vulnix badge generation
- Update dashboard HTML generation to only show lynis/neofetch columns

### Phase 4: Health Endpoint
- Update `get_health_status()` to only count lynis/neofetch in `reports_by_type`
- Remove Trivy/Vulnix keys from JSON response

### Phase 5: Documentation
- Update README.md to reflect only Lynis + Neofetch support
- Update CLAUDE.md context with new report types list
- Update test files to remove Trivy/Vulnix examples

## Risks / Trade-offs

### Risk: Breaking change for existing clients
- **Impact:** Clients currently submitting Trivy/Vulnix reports will receive HTTP 400 errors
- **Mitigation:** Clear error messages guide clients to update their scripts; document breaking change in release notes

### Risk: Historical dashboard data shows incomplete systems
- **Impact:** Systems with old Trivy/Vulnix reports but no recent Lynis scans will show as NOK
- **Mitigation:** Expected behavior; systems should run current Lynis scans for compliance

### Risk: Loss of container/NixOS-specific vulnerability tracking
- **Impact:** Trivy (containers) and Vulnix (NixOS) vulnerabilities no longer tracked
- **Mitigation:** Accepted trade-off for ISO compliance focus; Lynis provides sufficient hardening audit

### Trade-off: Data on disk but not displayed
- **Benefit:** Historical data preserved for manual review if needed
- **Cost:** Disk space used by files that aren't processed
- **Mitigation:** Document that old Trivy/Vulnix files can be manually deleted if disk space is a concern

## Migration Plan

### Pre-deployment
1. Identify all client systems currently submitting Trivy or Vulnix reports
2. Update client scan scripts to remove Trivy/Vulnix submission
3. Test updated client scripts against staging server

### Deployment
1. Stop Honeybadger server
2. Backup `honeybadger_server.py`
3. Deploy new version with Trivy/Vulnix support removed
4. Start server
5. Verify health endpoint returns expected report types

### Post-deployment
1. Monitor server logs for HTTP 400 errors (indicates clients still submitting Trivy/Vulnix)
2. Contact system owners of failing clients
3. Verify dashboard displays correctly with only Lynis/Neofetch

### Rollback
If critical issues arise:
1. Stop server
2. Restore backup `honeybadger_server.py`
3. Restart server
4. All functionality restored (existing reports remain on disk)

### Validation
- Server accepts Lynis reports: `curl -X POST -H "X-Report-Type: lynis" ...`
- Server accepts Neofetch reports: `curl -X POST -H "X-Report-Type: neofetch" ...`
- Server rejects Trivy reports: `curl -X POST -H "X-Report-Type: trivy" ...` → HTTP 400
- Server rejects Vulnix reports: `curl -X POST -H "X-Report-Type: vulnix" ...` → HTTP 400
- Dashboard shows only Lynis/Neofetch columns
- Health endpoint only counts lynis/neofetch in statistics

## Open Questions

None - requirements are clear and design is straightforward.
