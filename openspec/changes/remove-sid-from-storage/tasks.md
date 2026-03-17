## 1. ComplianceCache Modifications

- [x] 1.1 Update cache data structure: change key from `sid-username` to `hostname-username`
- [x] 1.2 Remove `sid` field from cache entry dictionaries
- [x] 1.3 Update cache.rebuild() to use hostname instead of SID when parsing directory names
- [x] 1.4 Update cache.update_system() signature: remove `sid` parameter, use `hostname` instead
- [x] 1.5 Update cache.update_system() to use `hostname-username` as cache key
- [x] 1.6 Update directory name parsing in rebuild(): parse `hostname-username` instead of `sid-username`

## 2. Report Storage Modifications

- [x] 2.1 Update save_report() signature: remove SID from return tuple
- [x] 2.2 Remove SID extraction logic from save_report() (lines ~548-563)
- [x] 2.3 Change compliance mode directory path to use `{hostname}-{username}` instead of `{sid}-{username}`
- [x] 2.4 Remove neofetch SID reading fallback logic for non-neofetch uploads
- [x] 2.5 Verify legacy mode storage remains unchanged (`hostname-username-YYYYMMDD`)
- [x] 2.6 Test directory creation with hostname containing valid characters
- [x] 2.7 Test overwrite behavior within same audit period using hostname-username

## 3. POST Handler Updates

- [x] 3.1 Update do_POST() to handle new save_report() return signature (no SID)
- [x] 3.2 Remove SID from success response JSON
- [x] 3.3 Update compliance cache call: pass hostname instead of SID
- [x] 3.4 Verify response includes: status, message, path, audit_period (compliance), os_type
- [x] 3.5 Test POST with various hostnames (alphanumeric, hyphens, underscores)
- [x] 3.6 Test POST in compliance mode returns correct hostname-based path
- [x] 3.7 Test POST in legacy mode returns correct date-based path

## 4. Compliance Dashboard Updates

- [x] 4.1 Update generate_compliance_dashboard_html() table headers: change "SID" to "Hostname"
- [x] 4.2 Update table data rendering: use `hostname` field instead of `sid`
- [x] 4.3 Update download URL generation: use `hostname-username` instead of `sid-username`
- [x] 4.4 Update JavaScript filter logic: remove SID references, use hostname (N/A - no filter in compliance dashboard)
- [x] 4.5 Update search placeholder text: remove "SID" mention (N/A - no search in compliance dashboard)
- [x] 4.6 Verify badge download links work with new hostname-based paths
- [x] 4.7 Test dashboard rendering with multiple systems in same period
- [x] 4.8 Test period switching preserves hostname-based display

## 5. Legacy Dashboard Updates

- [x] 5.1 Update generate_status_html() to remove SID column
- [x] 5.2 Update legacy table headers: remove SID column if present
- [x] 5.3 Update legacy table data rendering: remove SID field display
- [x] 5.4 Update legacy search/filter logic: remove SID references
- [x] 5.5 Verify legacy dashboard shows hostname and username correctly
- [x] 5.6 Test legacy mode with date-based directory structure

## 6. Neofetch SID Extraction Cleanup

- [x] 6.1 Remove SID extraction from do_GET() legacy dashboard report scanning (lines ~645-653)
- [x] 6.2 Remove `sid` field from report dictionaries in legacy mode
- [x] 6.3 Clean up any remaining references to `data.get('host')` for SID purposes
- [x] 6.4 Verify neofetch reports still validate correctly (no SID extraction during validation)

## 7. Integration Testing

- [x] 7.1 Test end-to-end upload flow: POST → storage → cache → dashboard
- [x] 7.2 Test compliance mode: upload to current period, verify hostname-based directory created
- [x] 7.3 Test legacy mode: upload, verify date-based directory created
- [x] 7.4 Test multiple uploads same audit period: verify overwrite behavior
- [x] 7.5 Test different hostnames same period: verify separate directories created
- [x] 7.6 Test same hostname different users: verify separate directories created
- [x] 7.7 Test dashboard display after uploads: verify hostname shown, no SID column
- [x] 7.8 Test report downloads: verify URLs work with hostname-based paths
- [x] 7.9 Test server restart: verify cache rebuilds correctly with hostname-based structure
- [x] 7.10 Test health endpoint: verify statistics update correctly

## 8. Manual Migration Preparation

- [x] 8.1 Document migration procedure in BUGFIXES.md or migration guide
- [x] 8.2 Provide command to find affected directories: `find reports/ -name "* *" -type d`
- [x] 8.3 Document manual move procedure for orphaned directories
- [x] 8.4 Create example migration script or commands
- [x] 8.5 Test migration on sample data before production deployment

## 9. Documentation Updates

- [x] 9.1 Update CLAUDE.md with line number changes if applicable
- [x] 9.2 Update README.md curl examples to reflect response changes (no SID field)
- [x] 9.3 Document breaking changes: storage paths, API response format
- [x] 9.4 Update known limitations: hostname+username must be unique
- [x] 9.5 Document cleanup procedure for directories with spaces

## 10. Verification and Cleanup

- [x] 10.1 Search codebase for remaining "sid" references: `grep -i "sid" honeybadger_server.py`
- [x] 10.2 Verify all removed references are intentional (keep any unrelated SID uses)
- [x] 10.3 Test all 4 report types upload correctly
- [x] 10.4 Verify compliance dashboard shows correct data after changes
- [x] 10.5 Verify legacy dashboard shows correct data after changes
- [x] 10.6 Run test suite if available (test_*.py files)
- [x] 10.7 Manual smoke test: upload reports, view dashboard, download reports
- [x] 10.8 Check server logs for any errors or warnings related to SID
