## Context

The honeybadger server currently stores reports in date-based directories (`hostname-username-YYYYMMDD/`) and displays a chronological list of all uploads. This works for ad-hoc reporting but doesn't support compliance tracking for ISO audits.

ISO policy requires endpoints to be audited 2x per year. IT team needs visibility into:
- Which systems have submitted complete report sets during audit periods
- Which systems are missing reports or have incomplete submissions
- Compliance status per audit period (e.g., March 2026, September 2026)

Current single-file architecture (honeybadger_server.py) must be maintained. The server will be deployed as a systemd service behind nginx, enabling long-running in-memory state.

## Goals / Non-Goals

**Goals:**
- Store reports organized by configurable audit periods (specific months)
- Track completeness of report sets (neofetch + lynis + trivy/vulnix)
- Provide period-based dashboard showing compliance status
- Support both legacy mode (date-based) and compliance mode via configuration
- Maintain single-file architecture
- Use in-memory cache for fast dashboard queries

**Non-Goals:**
- Migration of existing legacy reports to new structure (out of scope for v1)
- Export/reporting functionality (server is storage + display only)
- Automatic alerting or notifications
- Authentication/authorization (still out of scope)
- Client-side changes (X-OS-Type header is optional enhancement)

## Decisions

### Decision 1: Audit Period Storage Structure

**Choice:** Store reports in `{YYYY-MM}/{sid-username}/` directories where YYYY-MM is the audit month.

**Rationale:**
- Groups all reports for an audit period together (fast scanning)
- SID (from neofetch) is the stable system identifier (survives user changes)
- Separates different audit periods cleanly
- Allows same system to have reports in multiple periods

**Alternatives considered:**
- Keep date-based structure, compute compliance on-the-fly: Rejected due to performance (scanning all dates for each period view)
- Add metadata files alongside reports: Rejected to maintain simplicity, filesystem structure is self-documenting
- Use database (SQLite): Rejected to maintain "no database" principle

### Decision 2: Upload Date to Audit Period Mapping

**Choice:** Map upload to next audit month >= current month. If no audit month remains this year, use first audit month of next year.

**Algorithm:**
```python
def get_audit_period(upload_date, audit_months):
    future = [m for m in sorted(audit_months) if m >= upload_date.month]
    if future:
        return f"{upload_date.year}-{min(future):02d}"
    else:
        return f"{upload_date.year+1}-{min(audit_months):02d}"
```

**Rationale:**
- Uploads naturally accumulate toward the next audit period
- Example: April upload (between March and September) → September period
- Clear, deterministic mapping
- No "past period" ambiguity

**Alternatives considered:**
- Map to closest audit month (past or future): Rejected due to ambiguity in midpoint dates
- Allow uploads only during audit months: Rejected as too restrictive (users may scan early)

### Decision 3: In-Memory Compliance Cache

**Choice:** Maintain in-memory cache of compliance status, rebuilt on server start and updated on POST.

**Structure:**
```python
class ComplianceCache:
    data = {
        "2026-03": {
            "laptop-SN001-alice": {
                "sid": "laptop-SN001",
                "username": "alice",
                "os_type": "ubuntu",
                "upload_date": datetime(...),
                "reports": ["neofetch", "lynis", "trivy"],
                "is_complete": True,
                "missing": []
            },
            ...
        },
        ...
    }
```

**Rationale:**
- Fast dashboard rendering (no filesystem scan on every GET)
- Suitable for systemd deployment (long-running process)
- Updates incrementally on POST (no full rebuild needed)
- Acceptable memory footprint (50 systems × 2 periods = ~100 entries, <1MB)

**Alternatives considered:**
- Compute on-demand from filesystem: Works but slower, filesystem I/O on every request
- Persistent cache file: Adds sync complexity, not needed for systemd deployment
- No cache (always scan): Too slow for dashboard with many systems

### Decision 4: Dual Mode Operation (Legacy + Compliance)

**Choice:** Support both modes via `compliance.enabled` flag in config.yaml.

**When `compliance.enabled = false` (or absent):**
- Use legacy storage: `hostname-username-YYYYMMDD/`
- Show legacy dashboard (chronological list)
- No compliance tracking

**When `compliance.enabled = true`:**
- Use audit period storage: `YYYY-MM/sid-username/`
- Show compliance dashboard (period-based view)
- Build compliance cache

**Rationale:**
- Backwards compatibility for existing deployments
- Gradual migration path
- Clear separation of concerns

**Alternatives considered:**
- Always use new structure: Rejected due to breaking change for existing users
- Auto-detect mode from storage structure: Too implicit, config flag is clearer

### Decision 5: Report Completeness Definition

**Choice:** Complete set = neofetch + lynis + (trivy OR vulnix)

Configurable via:
```yaml
compliance:
  required_reports:
    mandatory: [neofetch, lynis]
    one_of: [trivy, vulnix]
```

**Rationale:**
- Neofetch required for system identity (SID)
- Lynis required for baseline security audit
- Trivy OR Vulnix accounts for different OS types (Ubuntu vs NixOS)
- Configuration allows future flexibility

**Alternatives considered:**
- OS-specific requirements (Ubuntu requires trivy, NixOS requires vulnix): Rejected as too complex for v1
- Fixed requirement (everyone needs all 4): Too restrictive
- No validation (accept any combination): Defeats compliance tracking purpose

### Decision 6: OS-Type Metadata Storage

**Choice:** Store os_type as in-memory metadata, sourced from optional `X-OS-Type` header.

**Rationale:**
- Useful for dashboard display (IT team can see OS distribution)
- Optional header (backwards compatible with existing clients)
- Stored only in cache, not persisted to filesystem (keeps storage simple)
- Future enhancement: could enable OS-specific validation

**Alternatives considered:**
- Parse from neofetch JSON: Possible but requires reading file on every upload
- Don't store OS type: Rejected, useful metadata for IT team
- Store in separate metadata file: Over-engineering for v1

## Risks / Trade-offs

### Risk: Existing reports invisible in compliance mode
- **Impact**: Legacy reports (date-based structure) won't show in new compliance dashboard
- **Mitigation**: Document clearly, provide migration guide (future), consider dual-mode dashboard view

### Risk: Clock skew affecting audit period mapping
- **Impact**: If server clock is wrong, uploads map to incorrect period
- **Mitigation**: Document requirement for accurate server time, consider logging upload date mapping

### Risk: Cache stale after server crash
- **Impact**: If server crashes mid-POST, cache may not reflect filesystem
- **Mitigation**: Cache rebuild on startup is fast (<1s for 100 systems), acceptable inconsistency window

### Risk: Memory usage with many systems
- **Impact**: 1000 systems × 4 periods = 4000 cache entries
- **Mitigation**: Monitor memory, estimate ~20KB per entry = ~80MB max for 4000 entries (acceptable)

### Risk: No migration path for existing data
- **Impact**: Old reports remain in legacy structure, won't appear in compliance view
- **Mitigation**: Document as known limitation for v1, future enhancement could add migration script

### Trade-off: Overwrite behavior within period
- **Pro**: Latest upload always reflects current state
- **Con**: Can't track "this system was complete but regressed to incomplete"
- **Mitigation**: Acceptable for v1, future could add audit log

### Trade-off: Compliance mode requires config change
- **Pro**: Explicit opt-in, backwards compatible
- **Con**: Requires manual configuration update
- **Mitigation**: Document clearly in README, provide example config

## Migration Plan

**Phase 1: Development**
1. Add config parsing for `compliance` section
2. Implement audit period calculation logic
3. Add dual-mode storage (legacy vs compliance)
4. Build ComplianceCache class
5. Create compliance dashboard HTML
6. Update POST handler for compliance mode
7. Update GET handler for dual dashboard

**Phase 2: Testing**
1. Test audit period mapping edge cases (year boundaries, etc.)
2. Test completeness validation (all combinations)
3. Test cache rebuild performance (simulate 100+ systems)
4. Test dual mode switching

**Phase 3: Deployment**
1. Deploy new server binary
2. Update config.yaml with compliance section
3. Set `compliance.enabled: true`
4. Restart service
5. Monitor logs for errors
6. Verify dashboard shows compliance view

**Rollback strategy:**
- Set `compliance.enabled: false` in config.yaml
- Restart service → falls back to legacy mode
- No data loss (legacy reports unaffected)

## Open Questions

1. **Should we add audit period "closing" logic?**
   - Currently periods remain open indefinitely
   - Could add `period_cutoff_days` to reject late uploads
   - Decision: Defer to future, keep simple for v1

2. **How to handle neofetch missing on upload?**
   - Can't determine SID without neofetch
   - Option A: Reject upload with error
   - Option B: Use hostname as fallback SID
   - **Tentative**: Option B for robustness, document as incomplete

3. **Dashboard default period selection?**
   - Show current/next audit period by default?
   - Or most recent period with data?
   - **Tentative**: Most recent period with data

4. **Auto-refresh in compliance mode?**
   - Removed from specs, but useful for monitoring
   - Could make configurable: `auto_refresh_seconds: 30`
   - **Tentative**: Add as optional config parameter
