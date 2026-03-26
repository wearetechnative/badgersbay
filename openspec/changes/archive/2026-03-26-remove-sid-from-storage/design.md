## Context

The compliance tracking feature (added in a previous change) introduced SID (System ID) extraction from neofetch reports to identify systems by their hardware model. The intent was to distinguish between multiple systems with the same hostname.

**Current SID extraction logic:**
```python
# From neofetch report
sid = data.get('host') or data.get('hostname') or hostname
```

**Problem:** The `host` field contains hardware model strings like `"LENOVO 21K9CTO1WW "` (note the trailing space), not a stable system identifier. This causes:
1. Directory names with spaces: `LENOVO 21K9CTO1WW -wtoorren/`
2. Filesystem path issues
3. Inconsistent tracking (same system creates multiple directories if neofetch isn't uploaded first)
4. Confusion in the dashboard (SID column shows hardware models, not system identifiers)

**Why hostname is sufficient:**
- Internal infrastructure use case: hostnames are typically unique
- If multiple systems share a hostname, that's a DNS/infrastructure problem to fix at the source
- Username already provides additional differentiation (same host, different users)
- Simpler is better: fewer moving parts, fewer failure modes

## Goals / Non-Goals

**Goals:**
- Remove all SID extraction and tracking logic
- Use only `hostname-username` for directory naming in compliance mode
- Maintain consistency: same system always uses same directory
- Simplify cache structure and dashboard displays
- Fix existing storage path issues (directories with spaces)

**Non-Goals:**
- Auto-migration of existing incorrectly-named directories (manual cleanup acceptable)
- Supporting multiple systems with identical hostname+username combination
- Changing legacy mode storage structure (remains `hostname-username-YYYYMMDD/`)

## Decisions

### Decision 1: Use hostname-username as the canonical identifier

**Rationale:**
- Hostname comes from `X-Hostname` header (or JSON field), controlled by the client
- More stable than neofetch's `host` field which varies by hardware
- Aligns with legacy mode's naming convention
- Simpler mental model: what you send in headers = what you get in storage

**Alternatives considered:**
- Keep SID but sanitize it (remove spaces, special chars) → Still unreliable, hardware model changes on replacement
- Use neofetch's `hostname` field instead of `host` → Still requires neofetch to be uploaded first
- Generate UUID for each system → Breaks human-readable storage, adds complexity

**Trade-off:** Systems with identical hostname+username will overwrite each other. This is acceptable because:
- It's a configuration error that should be fixed
- Internal infrastructure hostnames should be unique
- Simpler code is more valuable than handling edge cases

### Decision 2: Remove SID from all interfaces (API, cache, dashboard)

**Rationale:**
- No longer serves its intended purpose (stable system identification)
- Showing hardware model strings confuses users
- Hostname is more meaningful for operators

**Impact:**
- API responses remove `sid` field (breaking change, but compliance mode is new)
- Dashboard shows hostname instead of SID
- ComplianceCache uses `hostname-username` as key

### Decision 3: No automatic migration

**Rationale:**
- Consistent with existing approach (compliance-tracking change also didn't auto-migrate)
- Manual cleanup is safer (visibility into what's being changed)
- Few affected systems at this stage (compliance mode is recent)

**Migration path:**
1. Identify incorrectly-named directories (those with spaces or hardware models)
2. Move reports to correctly-named directories manually
3. Delete empty/orphaned directories

## Risks / Trade-offs

### [Risk] Multiple systems with same hostname+username
**Scenario:** Two laptops configured with identical hostname and same user account

**Mitigation:**
- This is already a configuration error (hostname uniqueness is standard practice)
- Document as a known limitation
- If it occurs, reports will overwrite (same as legacy mode behavior)
- Fix at infrastructure level (rename hosts)

### [Risk] Orphaned directories with spaces
**Scenario:** Existing `LENOVO 21K9CTO1WW -wtoorren/` directory contains reports

**Mitigation:**
- Document cleanup procedure in README
- Provide example command to find affected directories:
  ```bash
  find reports/ -name "* *" -type d
  ```
- Manual move is safe and visible

### [Risk] Breaking change for existing compliance mode users
**Scenario:** API clients expect `sid` field in response

**Mitigation:**
- Compliance mode is recent (just implemented)
- Limited deployment at this stage
- Update documentation and curl examples
- Version the API response if needed later

### [Trade-off] Hostname is not always globally unique
**Accepted limitation:**
- In internal infrastructure, hostnames should be unique per environment
- If not unique, that's an infrastructure problem to fix
- Simpler code that handles 99% case is better than complex code for 1% edge case

## Migration Plan

**Pre-deployment:**
1. Identify affected directories:
   ```bash
   find reports/2026-03 -name "* *" -type d
   ```

2. For each affected directory, manually move reports:
   ```bash
   # Example: move reports from hardware-model directory to hostname directory
   mv "reports/2026-03/LENOVO 21K9CTO1WW -wtoorren/"* "reports/2026-03/lobos-wtoorren/"
   rmdir "reports/2026-03/LENOVO 21K9CTO1WW -wtoorren/"
   ```

**Deployment:**
1. Stop server
2. Deploy new code
3. Start server (cache will rebuild with new structure)

**Post-deployment:**
1. Verify new uploads use correct paths
2. Monitor for any orphaned directories
3. Update client documentation if needed

**Rollback:**
- Revert code changes
- No data loss (filesystem unchanged except manual cleanup)
- Cache rebuilds automatically on restart
