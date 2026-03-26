# Manual Dashboard Refresh

**Status**: ✅ Implemented & Archived (2026-03-26)
**Priority**: Medium
**Effort**: 4-6 hours
**Risk**: Low

## Quick Summary

Replace automatic 30-second dashboard refresh with manual refresh button and rename "Compliance Rate" to "Coverage Rate" for accuracy.

## Problem

The dashboard currently auto-refreshes every 30 seconds, generating continuous HTTP GET requests. For compliance tracking (reports submitted during audit periods), real-time updates aren't critical. This creates unnecessary server load, especially with multiple concurrent users.

Additionally, "Compliance Rate" is misleading - it measures percentage of systems with complete reports, not organizational compliance.

## Solution

1. **Remove auto-refresh**: Delete JavaScript `setTimeout()` that calls `location.reload()` every 30 seconds
2. **Add refresh button**: User-triggered manual refresh in dashboard header
3. **Add timestamp**: Display "Last updated: HH:MM:SS" to show data freshness
4. **Rename metric**: Change "Compliance Rate" to "Coverage Rate" (more accurate)

## Impact

**Server Load Reduction**:
- **Before**: 10 users = 1,200 requests/hour (auto-refresh every 30s)
- **After**: 10 users = ~300 requests/hour (manual refresh ~5x per session)
- **Reduction**: ~75% fewer requests

**User Experience**:
- Users click "Refresh" to update data (acceptable for compliance use case)
- Timestamp shows data age, reducing confusion
- "Coverage Rate" accurately describes the metric
- No functionality lost

**Backwards Compatibility**:
- ✅ No API changes
- ✅ No configuration changes
- ✅ No deployment changes required
- ✅ Easy rollback (pure UI change)

## Files

- [`proposal.md`](./proposal.md) - Full proposal with rationale and alternatives
- [`design.md`](./design.md) - Detailed implementation design with code examples
- [`tasks.md`](./tasks.md) - 70 implementation and testing tasks across 10 groups

## Key Changes

### Code Changes

**File**: `honeybadger_server.py`

1. **Remove auto-refresh** (2 locations):
   - Line ~1375-1378 (legacy dashboard)
   - Line ~1657-1660 (compliance dashboard)

2. **Add refresh button UI**:
   - Dashboard header with button and timestamp
   - CSS styling for button, hover states, animations
   - JavaScript for refresh and timestamp display

3. **Rename metric** (1 location):
   - Line ~1279: "Compliance Rate" → "Coverage Rate"

4. **Remove messaging** (2 locations):
   - Line ~1370 (legacy dashboard)
   - Line ~1769 (compliance dashboard)

### Documentation Changes

- Remove "auto-refresh every 30 seconds" mentions
- Add manual refresh documentation
- Define "Coverage Rate" metric clearly
- Update screenshots if needed

## Testing Focus

- ✅ No automatic refreshes occur (wait 60+ seconds)
- ✅ Refresh button works in both dashboards
- ✅ Timestamp displays correctly
- ✅ "Coverage Rate" label visible
- ✅ All existing features work (filters, period selector, etc.)
- ✅ Server load measurably reduced

## Implementation Phases

1. **Phase 1**: Compliance dashboard (10 tasks)
2. **Phase 2**: Legacy dashboard (6 tasks)
3. **Phase 3**: Testing (41 tasks)
4. **Phase 4**: Documentation (7 tasks)
5. **Phase 5**: Code review (8 tasks)

## Success Criteria

- [ ] Zero automatic page reloads after 2+ minutes
- [ ] Functional refresh button on both dashboards
- [ ] "Coverage Rate" replaces "Compliance Rate"
- [ ] 50-75% reduction in server load for multi-user scenarios
- [ ] All existing dashboard features functional
- [ ] Documentation updated

## Why "Coverage Rate"?

**Current**: "Compliance Rate"
- ❌ Implies organizational compliance with security policies
- ❌ Suggests regulatory/policy adherence
- ❌ Doesn't accurately describe what's measured

**Proposed**: "Coverage Rate"
- ✅ Clearly indicates coverage of systems with reports
- ✅ Accurate: % of systems covered by complete report sets
- ✅ Industry-standard terminology for monitoring coverage
- ✅ Avoids confusion with compliance policies

**Calculation**:
```python
complete_systems = sum(1 for s in systems.values() if s['is_complete'])
coverage_rate = (complete_systems / total_systems * 100)
```

## Server Load Example

**Scenario**: 10 users viewing dashboard during audit period

### Before (Auto-Refresh)
```
10 users × 2 requests/minute = 20 requests/minute
20 × 60 minutes = 1,200 requests/hour
1,200 × 24 hours = 28,800 requests/day
```

### After (Manual Refresh)
```
10 users × ~0.5 requests/minute = 5 requests/minute
5 × 60 minutes = 300 requests/hour
300 × 24 hours = 7,200 requests/day

Reduction: 75%
```

**Benefits**:
- Reduced CPU (fewer HTML generations)
- Reduced filesystem scans (`get_reports_status()`)
- Reduced authentication checks
- Better scalability for more users

## Browser Compatibility

**Target**: Modern browsers (2021+)
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Features Used** (all universally supported):
- `location.reload()`
- CSS Flexbox
- CSS Animations
- JavaScript `Date` object
- `addEventListener()`

## Accessibility

- ✅ Keyboard navigation (Tab to button, Enter to activate)
- ✅ Screen reader support (aria-label, role="status")
- ✅ Visual feedback (hover, active, spinning icon)
- ✅ Clear button text ("Refresh")
- ✅ Timestamp context (no color-only indication)

## Security

**No new vulnerabilities**:
- Same `location.reload()` as before
- No new endpoints or APIs
- No authentication changes
- GET requests remain idempotent
- XSS risk unchanged

## Rollback Plan

If issues arise:
1. Revert Python file changes
2. Redeploy server
3. No configuration changes needed
4. **Total time: ~5 minutes**

Simple rollback due to:
- No API changes
- No storage changes
- No database migrations
- Pure UI modification

## Related Changes

- **`compliance-tracking`**: Introduced compliance dashboard (where manual refresh is most appropriate)
- **`add-authentication`**: Manual refresh aligns with deliberate dashboard access pattern
- **`remove-sid-from-storage`**: Independent storage changes

## Next Steps

1. **Review proposal**: Stakeholder approval
2. **Implementation**: Follow tasks.md (70 tasks)
3. **Testing**: Verify functionality and load reduction
4. **Documentation**: Update README.md
5. **Deploy**: Low-risk deployment (no breaking changes)

## Questions?

- **Why not configurable?** Manual refresh is simpler and sufficient for compliance use case
- **Why not increase interval?** Manual is cleaner than long-interval auto-refresh
- **Why not WebSockets?** Over-engineered for compliance tracking
- **Impact on monitoring?** None - `/health` endpoint unchanged

## References

- [OpenSpec Project](../../PROJECT.md)
- [Honeybadger Server README](../../../README.md)
- [Compliance Tracking Change](../compliance-tracking/)
