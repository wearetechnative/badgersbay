## 1. Validation Layer

- [x] 1.1 Update `valid_types` list to only include `['lynis', 'neofetch']`
- [x] 1.2 Remove Trivy validation logic from `validate_report_structure()` function
- [x] 1.3 Remove Vulnix validation logic from `validate_report_structure()` function
- [x] 1.4 Update validation error messages to only list `lynis, neofetch` as supported types
- [x] 1.5 Test that Trivy submissions are rejected with HTTP 400
- [x] 1.6 Test that Vulnix submissions are rejected with HTTP 400
- [x] 1.7 Test that Lynis submissions are still accepted
- [x] 1.8 Test that Neofetch submissions are still accepted

## 2. Storage Layer

- [x] 2.1 Update `save_report()` filename mapping to only handle lynis and neofetch
- [x] 2.2 Remove Trivy file handling code (if any conditional logic exists)
- [x] 2.3 Remove Vulnix file handling code (if any conditional logic exists)
- [x] 2.4 Test that Lynis reports are saved correctly
- [x] 2.5 Test that Neofetch reports are saved correctly

## 3. Dashboard Status Logic

- [x] 3.1 Update `get_reports_status()` to only check for lynis-report.json and neofetch-report.json files
- [x] 3.2 Update status calculation to: `is_ok = has_neofetch and has_lynis`
- [x] 3.3 Remove Trivy file existence checks
- [x] 3.4 Remove Vulnix file existence checks
- [x] 3.5 Test that systems with only Neofetch + Lynis show as OK (green)
- [x] 3.6 Test that systems missing Neofetch show as NOK (red)
- [x] 3.7 Test that systems missing Lynis show as NOK (red)

## 4. Dashboard Statistics

- [x] 4.1 Update statistics cards to only count Lynis and Neofetch reports
- [x] 4.2 Remove Trivy statistics card from HTML generation
- [x] 4.3 Remove Vulnix statistics card from HTML generation
- [x] 4.4 Update statistics calculation logic to only count lynis-report.json and neofetch-report.json
- [x] 4.5 Test that dashboard statistics only show counts for Lynis and Neofetch

## 5. Dashboard Report Badges

- [x] 5.1 Update badge generation to only create badges for Lynis and Neofetch
- [x] 5.2 Remove Trivy badge generation code
- [x] 5.3 Remove Vulnix badge generation code
- [x] 5.4 Ensure "Missing Neofetch" red badge still displays when appropriate
- [x] 5.5 Test that only Lynis and Neofetch badges appear for complete systems
- [x] 5.6 Test that existing Trivy/Vulnix files on disk don't create badges

## 6. Health Endpoint

- [x] 6.1 Update `get_health_status()` to only count Lynis and Neofetch in `reports_by_type`
- [x] 6.2 Remove Trivy counting logic
- [x] 6.3 Remove Vulnix counting logic
- [x] 6.4 Update health endpoint JSON response format (remove trivy/vulnix keys)
- [x] 6.5 Test health endpoint returns correct report type counts
- [x] 6.6 Test health endpoint no longer includes trivy or vulnix keys

## 7. Documentation

- [x] 7.1 Update README.md to only mention Lynis and Neofetch as supported types
- [x] 7.2 Update CLAUDE.md "Supported Report Types" section to remove Trivy and Vulnix
- [x] 7.3 Update CLAUDE.md "Domain Model" and status logic documentation
- [x] 7.4 Remove test-trivy-report.json from test files (or mark as obsolete)
- [x] 7.5 Update test.sh script to only test Lynis and Neofetch submissions
- [x] 7.6 Add migration notes documenting the breaking change

## 8. Integration Testing

- [x] 8.1 Start server and verify it accepts Lynis POST requests
- [x] 8.2 Start server and verify it accepts Neofetch POST requests
- [x] 8.3 Start server and verify it rejects Trivy POST requests with HTTP 400
- [x] 8.4 Start server and verify it rejects Vulnix POST requests with HTTP 400
- [x] 8.5 Verify dashboard displays correctly with only Lynis and Neofetch data
- [x] 8.6 Verify dashboard status logic marks systems OK only with Neofetch + Lynis
- [x] 8.7 Verify health endpoint returns correct statistics
- [x] 8.8 Test with existing report directories that have old Trivy/Vulnix files
