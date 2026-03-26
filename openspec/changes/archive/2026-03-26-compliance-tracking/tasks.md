## 1. Configuration and Setup

- [x] 1.1 Add compliance configuration section to config.yaml schema in Config class
- [x] 1.2 Parse compliance.enabled flag (default: false for backwards compatibility)
- [x] 1.3 Parse compliance.audit_months list (validate values 1-12)
- [x] 1.4 Parse compliance.required_reports.mandatory list (default: [neofetch, lynis])
- [x] 1.5 Parse compliance.required_reports.one_of list (default: [trivy, vulnix])
- [x] 1.6 Add config validation with clear error messages for invalid audit months

## 2. Audit Period Calculation

- [x] 2.1 Implement get_audit_period(upload_date, audit_months) function
- [x] 2.2 Test audit period mapping for uploads during audit month
- [x] 2.3 Test audit period mapping for uploads between audit months
- [x] 2.4 Test audit period mapping for uploads after last audit month of year
- [x] 2.5 Test audit period mapping for uploads before first audit month of year
- [x] 2.6 Add unit tests for year boundary edge cases

## 3. Storage Layer Modifications

- [x] 3.1 Modify save_report() to check compliance mode flag
- [x] 3.2 Implement compliance-mode path generation: {audit-period}/{sid-username}/
- [x] 3.3 Extract SID from neofetch report (use hostname as fallback if missing)
- [x] 3.4 Implement legacy-mode path generation: {hostname-username-YYYYMMDD}/
- [x] 3.5 Update directory creation to handle audit period structure
- [x] 3.6 Update file naming to remain {report-type}-report.json in both modes
- [x] 3.7 Test overwrite behavior within same audit period
- [x] 3.8 Test separate storage for different audit periods

## 4. Report Completeness Validation

- [x] 4.1 Implement check_completeness(reports, config) function
- [x] 4.2 Validate mandatory reports present (neofetch, lynis)
- [x] 4.3 Validate at least one scanner from one_of list present
- [x] 4.4 Generate list of missing reports for incomplete sets
- [x] 4.5 Test completeness with trivy (should pass)
- [x] 4.6 Test completeness with vulnix (should pass)
- [x] 4.7 Test completeness with both trivy and vulnix (should pass)
- [x] 4.8 Test incomplete scenarios (missing lynis, missing scanner, etc.)

## 5. In-Memory Compliance Cache

- [x] 5.1 Create ComplianceCache class with data dictionary structure
- [x] 5.2 Implement cache.rebuild() to scan filesystem and populate cache
- [x] 5.3 Implement cache.update_system() to update single entry on POST
- [x] 5.4 Implement cache.get_period_status(audit_period) to retrieve period data
- [x] 5.5 Initialize global cache instance on server startup
- [x] 5.6 Call cache.rebuild() in run_server() after storage directory creation
- [x] 5.7 Test cache rebuild with empty storage
- [x] 5.8 Test cache rebuild with multiple audit periods and systems
- [x] 5.9 Test cache update on new upload
- [x] 5.10 Verify cache performance with 50+ systems

## 6. POST Handler Updates

- [x] 6.1 Add X-OS-Type header extraction in do_POST()
- [x] 6.2 Pass os_type to save_report() function
- [x] 6.3 Calculate audit_period in compliance mode
- [x] 6.4 Update cache after successful report save in compliance mode
- [x] 6.5 Include audit_period in success response for compliance mode
- [x] 6.6 Include os_type in success response
- [x] 6.7 Test POST with X-OS-Type header
- [x] 6.8 Test POST without X-OS-Type header (should default to "unknown")
- [x] 6.9 Verify cache updates correctly after POST

## 7. Compliance Dashboard HTML

- [x] 7.1 Create generate_compliance_dashboard_html() function
- [x] 7.2 Add audit period selector dropdown with available periods
- [x] 7.3 Display summary statistics (total, complete, incomplete, percentage)
- [x] 7.4 Create compliance table with columns: SID, Username, OS Type, Upload Date, Reports, Status
- [x] 7.5 Implement report badges display (N L T V)
- [x] 7.6 Implement status indicators (✓ Complete, ⚠ Incomplete, ✗ Missing)
- [x] 7.7 Display missing reports for incomplete systems
- [x] 7.8 Add filter dropdown (All, Complete, Incomplete)
- [x] 7.9 Implement JavaScript period switching (update URL param and reload)
- [x] 7.10 Implement JavaScript filter functionality
- [x] 7.11 Update download links to work with audit-period-based paths
- [x] 7.12 Add CSS styling for compliance dashboard
- [x] 7.13 Test dashboard rendering with various data scenarios

## 8. GET Handler Updates

- [x] 8.1 Modify do_GET() to check compliance mode flag
- [x] 8.2 Route to generate_compliance_dashboard_html() if compliance enabled
- [x] 8.3 Route to generate_status_html() (legacy) if compliance disabled
- [x] 8.4 Parse audit_period query parameter from URL
- [x] 8.5 Default to most recent period with data if no parameter
- [x] 8.6 Update report download path handling for audit-period structure
- [x] 8.7 Maintain path traversal security checks for new structure
- [x] 8.8 Test GET / with compliance enabled
- [x] 8.9 Test GET / with compliance disabled (legacy mode)
- [x] 8.10 Test report downloads from compliance-mode paths

## 9. Integration Testing

- [x] 9.1 Test end-to-end: upload → storage → cache → dashboard display
- [x] 9.2 Test with audit_months [3, 9] configuration
- [x] 9.3 Test uploads in different months mapping correctly
- [x] 9.4 Test multiple systems uploading to same period
- [x] 9.5 Test same system uploading to different periods
- [x] 9.6 Test incomplete uploads and dashboard display
- [x] 9.7 Test switching between audit periods in dashboard
- [x] 9.8 Test filter functionality (show only incomplete)
- [x] 9.9 Test server restart and cache rebuild
- [x] 9.10 Verify legacy mode still works (backwards compatibility)

## 10. Documentation and Configuration

- [x] 10.1 Update README.md with compliance mode documentation
- [x] 10.2 Add example compliance configuration to README
- [x] 10.3 Document audit period mapping logic
- [x] 10.4 Document report completeness requirements
- [x] 10.5 Update config.yaml with commented compliance section example
- [x] 10.6 Document X-OS-Type header usage for clients
- [x] 10.7 Add migration notes for existing deployments
- [x] 10.8 Document known limitations (no legacy data migration)
