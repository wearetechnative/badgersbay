## Why

The dashboard currently auto-refreshes every 30 seconds using JavaScript `location.reload()`, which generates continuous HTTP GET requests to the server. For compliance tracking use cases, real-time updates are not critical - compliance status changes only when systems submit new reports, which typically happens during audit periods (e.g., twice per year). The automatic refresh creates unnecessary server load, especially for EC2 instances serving multiple users viewing the dashboard simultaneously.

Additionally, the "Compliance Rate" metric name is misleading - it measures the percentage of systems that have submitted complete report sets, not organizational compliance with security policies. A more accurate name would better communicate what the metric represents.

## What Changes

- **Remove 30-second auto-refresh**: Remove JavaScript `setTimeout()` that calls `location.reload()` every 30 seconds
- **Add manual refresh button**: Add a "Refresh" button in the dashboard UI to allow users to manually reload data
- **Rename "Compliance Rate" metric**: Change to "Coverage Rate" to accurately reflect that it measures the percentage of systems with complete report submissions
- **Update refresh info text**: Change "Page automatically refreshes every 30 seconds" to indicate manual refresh is available
- **Add refresh timestamp**: Display "Last updated: HH:MM:SS" to show when data was last loaded

## Capabilities

### Modified Capabilities
- `compliance-dashboard`: Remove auto-refresh, add manual refresh button with timestamp
- `status-dashboard`: Remove auto-refresh (legacy dashboard also uses 30-second reload)

### New Capabilities
- `manual-refresh-ui`: User-triggered dashboard refresh via button instead of automatic timer

## Impact

**Code:**
- Remove JavaScript `setTimeout()` and `location.reload()` calls from both compliance and legacy dashboard HTML
- Add "Refresh" button to dashboard header
- Add JavaScript to display current timestamp and update on manual refresh
- Change "Compliance Rate" label to "Coverage Rate" in HTML template
- Update `.stat-label` content from "Compliance Rate" to "Coverage Rate"

**Server Load:**
- Significant reduction in HTTP GET requests to dashboard endpoint
- Example: 10 simultaneous users = 10 requests/30s (1200 requests/hour) → 0 automatic requests
- Actual load depends on user behavior (manual refresh frequency)
- Health check endpoint (`/health`) remains unchanged for automated monitoring

**User Experience:**
- Users must click "Refresh" button to see updated data (acceptable for compliance use case)
- Timestamp shows when data was last loaded, reducing confusion
- "Coverage Rate" more accurately describes the metric (% of systems with complete reports)
- No functional capability lost - all data remains accessible

**Backwards Compatibility:**
- Fully backwards compatible - no API changes
- No configuration changes required
- No impact on report submission or authentication
- Dashboard behavior change only (no server-side logic changes)

**Documentation:**
- Update README.md to reflect manual refresh behavior
- Remove mentions of "auto-refresh every 30 seconds"
- Update screenshots if they show auto-refresh messaging
- Clarify "Coverage Rate" metric meaning in documentation

## Alternatives Considered

**1. Configurable auto-refresh interval**
- Could add `auto_refresh_seconds: 0` config option (0 = disabled)
- Rejected: Adds configuration complexity for a feature that's not needed for compliance tracking
- Manual refresh is simpler and more appropriate for the use case

**2. Keep auto-refresh but increase interval (e.g., 5 minutes)**
- Would reduce load compared to 30 seconds
- Rejected: Still generates unnecessary requests; manual refresh is cleaner solution

**3. WebSocket-based live updates**
- Would only push updates when reports are submitted
- Rejected: Over-engineered for compliance tracking; adds significant complexity

## Implementation Notes

**Metric Renaming Justification:**
- Current: "Compliance Rate" implies organizational compliance with security policies
- Reality: Measures percentage of systems that have uploaded complete report sets
- Better names considered:
  - ✅ **"Coverage Rate"** - Best choice: clearly indicates coverage of systems with reports
  - "Completion Rate" - Good, but could be confused with individual system completion
  - "Report Coverage" - Too generic
  - "Audit Coverage" - Implies broader audit scope than just report submission

**Files to Modify:**
- `honeybadger_server.py`:
  - Line ~1375-1378: Remove auto-refresh JavaScript from legacy dashboard
  - Line ~1657-1660: Remove auto-refresh JavaScript from compliance dashboard
  - Line ~1279: Change "Compliance Rate" to "Coverage Rate"
  - Line ~1370 & 1769: Update refresh info text
  - Add refresh button HTML and timestamp display logic
  - Add JavaScript for manual refresh functionality

**Backward Compatibility:**
- No breaking changes to API, configuration, or deployment
- Pure UI/UX change in dashboard rendering
- Can be deployed without any client or configuration updates

## Success Criteria

- [ ] Dashboard no longer auto-refreshes every 30 seconds
- [ ] "Refresh" button present and functional on both compliance and legacy dashboards
- [ ] "Last updated" timestamp displays correctly and updates on manual refresh
- [ ] Metric label changed from "Compliance Rate" to "Coverage Rate"
- [ ] No auto-refresh messaging present in UI
- [ ] Health check endpoint remains unchanged (no impact on automated monitoring)
- [ ] Documentation updated to reflect manual refresh behavior
- [ ] Server load measurably reduced for multi-user scenarios

## Related Changes

This change is independent but complements:
- `compliance-tracking`: Compliance dashboard where auto-refresh is least needed
- `add-authentication`: Manual refresh aligns with deliberate dashboard access pattern
