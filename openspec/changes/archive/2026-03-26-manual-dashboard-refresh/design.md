# Design: Manual Dashboard Refresh

## Overview

Replace automatic 30-second dashboard refresh with manual refresh button to reduce server load while maintaining full dashboard functionality.

## Current Implementation

### Auto-Refresh Mechanism

**Legacy Dashboard** (`honeybadger_server.py:1375-1378`):
```javascript
// Auto-refresh every 30 seconds
setTimeout(function() {
    location.reload();
}, 30000);
```

**Compliance Dashboard** (`honeybadger_server.py:1657-1660`):
```javascript
setTimeout(function() {
    location.reload();
}, 30000);
```

**User Messaging**:
- Line 1370: `<small style="color: #999; margin-top: 5px;">Page automatically refreshes every 30 seconds</small>`
- Line 1769: `<div class="refresh-info">Page automatically refreshes every 30 seconds</div>`

### Compliance Rate Metric

**Display** (`honeybadger_server.py:1278-1280`):
```html
<div class="stat-card">
    <div class="stat-number">{complete_pct:.0f}%</div>
    <div class="stat-label">Compliance Rate</div>
</div>
```

**Calculation** (`honeybadger_server.py:1158-1160`):
```python
complete_systems = sum(1 for s in systems.values() if s['is_complete'])
incomplete_systems = total_systems - complete_systems
complete_pct = (complete_systems / total_systems * 100) if total_systems > 0 else 0
```

## Proposed Changes

### 1. Remove Auto-Refresh

**Action**: Delete `setTimeout()` blocks from both dashboards

**Legacy Dashboard**:
```diff
-        // Auto-refresh every 30 seconds
-        setTimeout(function() {
-            location.reload();
-        }, 30000);
```

**Compliance Dashboard**:
```diff
-        setTimeout(function() {
-            location.reload();
-        }, 30000);
```

### 2. Add Manual Refresh Button

**Location**: Dashboard header, next to title

**HTML Structure**:
```html
<div class="dashboard-header">
    <div class="header-content">
        <h1>Compliance Dashboard - {period_display}</h1>
        <div class="header-actions">
            <button id="refreshBtn" class="refresh-btn" onclick="refreshDashboard()">
                <span class="refresh-icon">🔄</span> Refresh
            </button>
            <span id="lastUpdated" class="last-updated">Last updated: {timestamp}</span>
        </div>
    </div>
</div>
```

**CSS Styling**:
```css
.dashboard-header {
    background: white;
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 15px;
}

.refresh-btn {
    background: #0066cc;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    transition: background 0.2s;
}

.refresh-btn:hover {
    background: #0052a3;
}

.refresh-btn:active {
    transform: scale(0.98);
}

.refresh-icon {
    display: inline-block;
    transition: transform 0.5s;
}

.refresh-btn.refreshing .refresh-icon {
    animation: spin 0.5s linear;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
}

.last-updated {
    color: #666;
    font-size: 13px;
    font-style: italic;
}
```

**JavaScript**:
```javascript
function refreshDashboard() {
    const btn = document.getElementById('refreshBtn');
    btn.classList.add('refreshing');
    btn.disabled = true;
    location.reload();
}

function updateTimestamp() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    const timestamp = `${hours}:${minutes}:${seconds}`;

    const elem = document.getElementById('lastUpdated');
    if (elem) {
        elem.textContent = `Last updated: ${timestamp}`;
    }
}

// Set timestamp on page load
document.addEventListener('DOMContentLoaded', updateTimestamp);
```

### 3. Rename Metric

**Change Label**:
```diff
 <div class="stat-card">
     <div class="stat-number">{complete_pct:.0f}%</div>
-    <div class="stat-label">Compliance Rate</div>
+    <div class="stat-label">Coverage Rate</div>
 </div>
```

**Rationale**:
- "Coverage Rate" accurately describes the metric: percentage of systems covered by complete reports
- Avoids confusion with organizational compliance policies
- Aligns with industry terminology for monitoring coverage

### 4. Update User Messaging

**Remove Auto-Refresh Text**:
```diff
-<small style="color: #999; margin-top: 5px;">Page automatically refreshes every 30 seconds</small>
```

```diff
-<div class="refresh-info">
-    Page automatically refreshes every 30 seconds
-</div>
```

**Add Manual Refresh Guidance** (optional):
```html
<div class="info-message">
    <span class="info-icon">ℹ️</span>
    Click "Refresh" to load latest report data
</div>
```

## Implementation Steps

### Phase 1: Compliance Dashboard
1. Remove auto-refresh JavaScript block (line ~1657-1660)
2. Add dashboard header with refresh button
3. Add CSS styling for button and timestamp
4. Add JavaScript functions for refresh and timestamp
5. Change "Compliance Rate" to "Coverage Rate" (line ~1279)
6. Remove auto-refresh messaging (line ~1769)

### Phase 2: Legacy Dashboard
1. Remove auto-refresh JavaScript block (line ~1375-1378)
2. Add refresh button to legacy dashboard header
3. Reuse CSS/JavaScript from compliance dashboard
4. Remove auto-refresh messaging (line ~1370)

### Phase 3: Testing
1. Verify refresh button works in both dashboards
2. Verify timestamp updates correctly
3. Confirm no automatic refreshes occur
4. Test with multiple concurrent users (measure server load reduction)
5. Verify all existing functionality still works (filters, period selector, etc.)

## Server Load Impact

### Before (Auto-Refresh)

**Scenario**: 10 concurrent users viewing dashboard

- Requests per user: 1 request per 30 seconds = 2 requests/minute
- Total requests: 10 users × 2 requests/minute = 20 requests/minute
- Hourly: 1,200 requests/hour
- Daily: 28,800 requests/day

**Scenario**: 50 concurrent users during audit period

- Requests per minute: 100 requests/minute
- Hourly: 6,000 requests/hour
- Daily: 144,000 requests/day

### After (Manual Refresh)

**Assumptions**:
- Users refresh dashboard ~5 times during session
- Average session: 10 minutes
- Same 10 concurrent users

**Realistic Usage**:
- Requests per user: 5 refreshes per 10-minute session = 0.5 requests/minute
- Total requests: 10 users × 0.5 requests/minute = 5 requests/minute
- Hourly: 300 requests/hour (75% reduction)
- Daily: 7,200 requests/day (75% reduction)

**Conservative Usage** (frequent manual refreshes):
- Users refresh every 2 minutes: ~5 refreshes per 10 minutes
- Still: 5 requests/minute (same as automatic)
- No worse than automatic refresh, users control frequency

### Load Reduction Benefits

1. **CPU/Memory**: Fewer dashboard HTML generations
2. **Authentication**: Fewer Basic Auth validations
3. **Filesystem**: Fewer directory scans (`get_reports_status()`)
4. **Network**: Reduced bandwidth for dashboard HTML delivery
5. **Scalability**: Better support for larger number of concurrent users

## Edge Cases

### Case 1: User Expects Real-Time Updates

**Issue**: User assumes dashboard updates automatically
**Solution**:
- "Last updated" timestamp makes stale data obvious
- Optional: Add browser notification API to alert on new reports (future enhancement)
- Documentation clearly states manual refresh required

### Case 2: Long-Running Session

**Issue**: User leaves dashboard open for hours without refreshing
**Solution**:
- Timestamp shows how old data is
- No functional problem - data doesn't expire or become invalid
- User can refresh anytime to see latest

### Case 3: Multi-Tab Behavior

**Issue**: User opens dashboard in multiple tabs
**Solution**:
- Each tab operates independently
- Each refresh affects only that tab
- No synchronization needed between tabs

### Case 4: Network/Server Error During Refresh

**Issue**: Refresh button clicked but server unreachable
**Solution**:
- Browser's native `location.reload()` handles network errors
- User sees standard browser error page
- Existing error handling mechanisms apply

## Accessibility Considerations

**Keyboard Navigation**:
- Refresh button must be keyboard-accessible (`<button>` element provides this)
- Add `aria-label` for screen readers: `aria-label="Refresh dashboard data"`

**Screen Readers**:
- Announce timestamp updates: `<span role="status" aria-live="polite">Last updated: {time}</span>`
- Button text clearly indicates action: "Refresh"

**Visual Indicators**:
- Button changes appearance on hover (existing CSS)
- Spinning icon during refresh provides visual feedback
- Timestamp provides context without color-only indication

## Browser Compatibility

**Target Support**: Modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)

**Features Used**:
- `location.reload()`: Universal support
- CSS Flexbox: Universal support in target browsers
- CSS Animations: Universal support
- `Date` object: Universal support
- `addEventListener()`: Universal support

**Fallback**: Not needed - all features have universal support in target browsers

## Security Considerations

**No New Vulnerabilities**:
- Manual refresh uses same `location.reload()` as automatic refresh
- No new endpoints or API changes
- No new authentication requirements
- XSS risk unchanged (all HTML is server-generated, no user input in JavaScript)

**CSRF Protection**:
- GET requests remain idempotent (read-only)
- Authentication still required (HTTP Basic Auth)
- No state changes occur on refresh

## Testing Checklist

- [ ] Refresh button renders correctly on compliance dashboard
- [ ] Refresh button renders correctly on legacy dashboard
- [ ] Button click triggers page reload
- [ ] Timestamp displays correctly on page load
- [ ] Timestamp format is HH:MM:SS
- [ ] No automatic refreshes occur (wait 2+ minutes)
- [ ] "Compliance Rate" renamed to "Coverage Rate"
- [ ] Auto-refresh messaging removed from both dashboards
- [ ] Keyboard navigation works (Tab to button, Enter to activate)
- [ ] Button hover state works
- [ ] Spinning animation works during refresh
- [ ] Multi-tab scenario: Each tab refreshes independently
- [ ] All existing dashboard features work (filters, period selector, download links)
- [ ] Server load reduced (measure with monitoring tools)

## Documentation Updates

**README.md**:
- Remove all mentions of "auto-refresh every 30 seconds"
- Add section about manual refresh button
- Update dashboard screenshots if they show auto-refresh text
- Clarify "Coverage Rate" metric definition

**CLAUDE.md** (if applicable):
- Update development context with manual refresh pattern
- Document rationale for removing auto-refresh

**Config Examples**:
- No changes needed (purely UI change)

## Future Enhancements

**1. Browser Notifications** (optional):
- Use Browser Notification API to alert users when new reports arrive
- Requires WebSocket or Server-Sent Events for push notifications
- Out of scope for this change

**2. Configurable Refresh Interval** (optional):
- Add `dashboard_refresh_seconds: 0` to config.yaml (0 = manual only)
- Allow users to opt into auto-refresh if desired
- Low priority - manual refresh is sufficient

**3. Refresh Keyboard Shortcut** (optional):
- Add `Ctrl+R` or `F5` hint in UI
- Standard browser behavior already supports this
- Low priority - native browser shortcuts work

## Rollback Plan

If issues arise:
1. Revert Python file changes (restore auto-refresh JavaScript)
2. Redeploy server
3. No database or configuration migration needed
4. No client-side changes required

Simple rollback due to no API or storage changes.
