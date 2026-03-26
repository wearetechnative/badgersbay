# Implementation Tasks: Manual Dashboard Refresh

## Status: ✅ Implemented (2026-03-26)

## Task Groups

### 1. Code Changes - Compliance Dashboard

**Objective**: Replace auto-refresh with manual refresh button in compliance dashboard

- [ ] 1.1 Remove auto-refresh JavaScript block (line ~1657-1660)
- [ ] 1.2 Add dashboard header HTML structure with refresh button
- [ ] 1.3 Add CSS styling for refresh button and header
- [ ] 1.4 Add CSS animation for spinning refresh icon
- [ ] 1.5 Add JavaScript `refreshDashboard()` function
- [ ] 1.6 Add JavaScript `updateTimestamp()` function
- [ ] 1.7 Add DOMContentLoaded event listener for timestamp initialization
- [ ] 1.8 Change "Compliance Rate" label to "Coverage Rate" (line ~1279)
- [ ] 1.9 Remove auto-refresh info text (line ~1769)
- [ ] 1.10 Add accessibility attributes (aria-label, role="status")

### 2. Code Changes - Legacy Dashboard

**Objective**: Apply same changes to legacy dashboard for consistency

- [ ] 2.1 Remove auto-refresh JavaScript block (line ~1375-1378)
- [ ] 2.2 Add dashboard header HTML structure with refresh button
- [ ] 2.3 Reuse CSS styling from compliance dashboard
- [ ] 2.4 Add JavaScript refresh and timestamp functions
- [ ] 2.5 Remove auto-refresh info text (line ~1370)
- [ ] 2.6 Add accessibility attributes

### 3. Testing - Functional

**Objective**: Verify all functionality works correctly

- [ ] 3.1 Test refresh button click triggers page reload (compliance dashboard)
- [ ] 3.2 Test refresh button click triggers page reload (legacy dashboard)
- [ ] 3.3 Verify timestamp displays on page load
- [ ] 3.4 Verify timestamp format is HH:MM:SS
- [ ] 3.5 Verify "Last updated" text is present
- [ ] 3.6 Verify button hover effect works
- [ ] 3.7 Verify spinning animation during refresh
- [ ] 3.8 Verify button disabled state during refresh
- [ ] 3.9 Confirm "Coverage Rate" label appears instead of "Compliance Rate"
- [ ] 3.10 Confirm no auto-refresh messaging visible

### 4. Testing - Auto-Refresh Removal

**Objective**: Confirm automatic refresh no longer occurs

- [ ] 4.1 Load compliance dashboard, wait 60 seconds, verify no automatic reload
- [ ] 4.2 Load legacy dashboard, wait 60 seconds, verify no automatic reload
- [ ] 4.3 Check browser DevTools Network tab - no unexpected requests after initial load
- [ ] 4.4 Monitor server logs - no GET requests without user interaction
- [ ] 4.5 Test with multiple tabs open - each tab behaves independently

### 5. Testing - Accessibility

**Objective**: Verify keyboard and screen reader support

- [ ] 5.1 Tab navigation reaches refresh button
- [ ] 5.2 Enter key activates refresh button
- [ ] 5.3 Screen reader announces button label correctly
- [ ] 5.4 Screen reader announces timestamp updates (aria-live)
- [ ] 5.5 Focus visible on button (keyboard navigation indicator)

### 6. Testing - Existing Features

**Objective**: Ensure no regressions in existing functionality

- [ ] 6.1 Compliance dashboard: Period selector dropdown works
- [ ] 6.2 Compliance dashboard: Filter dropdown (All/Complete/Incomplete) works
- [ ] 6.3 Compliance dashboard: Table displays correctly
- [ ] 6.4 Compliance dashboard: Report download links work
- [ ] 6.5 Legacy dashboard: Date-based filtering works
- [ ] 6.6 Legacy dashboard: Table displays correctly
- [ ] 6.7 Legacy dashboard: Report download links work
- [ ] 6.8 Authentication still required for dashboard access
- [ ] 6.9 Health check endpoint unaffected (/health)

### 7. Testing - Load/Performance

**Objective**: Measure server load reduction

- [ ] 7.1 Baseline test: Measure GET requests per minute with 10 simulated users (current auto-refresh)
- [ ] 7.2 Measure CPU usage with 10 concurrent users viewing dashboard (before)
- [ ] 7.3 Deploy manual refresh version
- [ ] 7.4 Measure GET requests per minute with 10 simulated users (manual refresh, realistic usage)
- [ ] 7.5 Measure CPU usage with 10 concurrent users viewing dashboard (after)
- [ ] 7.6 Calculate percentage reduction in requests
- [ ] 7.7 Document load reduction in test results

### 8. Testing - Edge Cases

**Objective**: Handle unusual scenarios gracefully

- [ ] 8.1 Test with slow network connection - button disabled until reload completes
- [ ] 8.2 Test with server offline - browser shows standard error page
- [ ] 8.3 Test with multiple tabs open - each tab refreshes independently
- [ ] 8.4 Test leaving dashboard open for 1+ hour - timestamp shows age correctly
- [ ] 8.5 Test rapid clicking of refresh button - no issues with double-refresh

### 9. Documentation Updates

**Objective**: Update all documentation to reflect changes

- [ ] 9.1 Update README.md: Remove "auto-refresh every 30 seconds" text
- [ ] 9.2 Update README.md: Add "Manual Refresh" section
- [ ] 9.3 Update README.md: Document "Coverage Rate" metric meaning
- [ ] 9.4 Update README.md: Add screenshot showing refresh button (optional)
- [ ] 9.5 Update CLAUDE.md: Document rationale for manual refresh pattern (if applicable)
- [ ] 9.6 Update openspec/PROJECT.md: Remove auto-refresh from feature list (if present)
- [ ] 9.7 Check for any other docs mentioning auto-refresh

### 10. Code Review & Quality

**Objective**: Ensure code quality and maintainability

- [ ] 10.1 Code review: HTML structure follows existing patterns
- [ ] 10.2 Code review: CSS follows existing styling conventions
- [ ] 10.3 Code review: JavaScript is clean and well-commented
- [ ] 10.4 Code review: No hardcoded values (use configuration where appropriate)
- [ ] 10.5 Code review: Accessibility attributes present and correct
- [ ] 10.6 Code review: No console.log statements left in production code
- [ ] 10.7 Verify Python file formatting (indentation, line length)
- [ ] 10.8 Run linters if available (pylint, flake8)

## Task Summary

- **Total Tasks**: 70
- **Completed**: 0
- **In Progress**: 0
- **Blocked**: 0
- **Not Started**: 70

## Implementation Groups

| Group | Tasks | Focus Area |
|-------|-------|------------|
| 1 | 10 | Compliance Dashboard Code |
| 2 | 6 | Legacy Dashboard Code |
| 3 | 10 | Functional Testing |
| 4 | 5 | Auto-Refresh Removal Testing |
| 5 | 5 | Accessibility Testing |
| 6 | 9 | Regression Testing |
| 7 | 7 | Load/Performance Testing |
| 8 | 5 | Edge Case Testing |
| 9 | 7 | Documentation |
| 10 | 8 | Code Review & Quality |

## Critical Path

1. **Group 1** (Compliance Dashboard) → **Group 3** (Functional Testing) → **Group 4** (Auto-Refresh Removal)
2. **Group 2** (Legacy Dashboard) → **Group 3** (Functional Testing)
3. **Group 7** (Load Testing) requires both dashboards complete
4. **Group 9** (Documentation) can proceed in parallel with testing

## Dependencies

- Group 2 can reuse CSS/JavaScript from Group 1
- Group 7 (Load Testing) requires Groups 1-2 complete
- Group 9 (Documentation) can start after Groups 1-2 design complete
- Group 10 (Code Review) should occur before final deployment

## Testing Strategy

**Manual Testing**:
- Groups 3, 4, 5, 6, 8 (requires human interaction and observation)

**Automated Testing** (future):
- Could add Selenium tests for button click, timestamp display
- Could add load testing scripts for Group 7
- Out of scope for initial implementation

**Browser Testing Matrix**:
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Deployment Plan

1. **Development**: Implement Groups 1-2 on development branch
2. **Testing**: Complete Groups 3-8 on staging environment
3. **Documentation**: Complete Group 9
4. **Review**: Complete Group 10
5. **Staging Deploy**: Deploy to staging, verify all tests pass
6. **Production Deploy**: Deploy to production during low-traffic period
7. **Monitor**: Watch server metrics for 24 hours post-deployment

## Rollback Procedure

If critical issues arise:

1. Revert commit in git
2. Redeploy previous version
3. No database changes required
4. No configuration changes required
5. Total rollback time: ~5 minutes

## Success Metrics

- [ ] Zero automatic page reloads after 2+ minutes of inactivity
- [ ] Refresh button functional on both dashboards
- [ ] "Coverage Rate" label visible instead of "Compliance Rate"
- [ ] Server load reduced by 50-75% for multi-user scenarios
- [ ] All existing dashboard features functional
- [ ] No accessibility regressions
- [ ] Documentation complete and accurate

## Notes

**Estimated Effort**: 4-6 hours
- Coding: 2 hours
- Testing: 2-3 hours
- Documentation: 1 hour
- Code review: 30 minutes

**Risk Level**: Low
- No API changes
- No database changes
- No configuration changes
- Pure UI/UX change
- Easy rollback

**Priority**: Medium
- Improves server performance
- Improves metric clarity ("Coverage Rate")
- Non-breaking change
- Can be deployed anytime
