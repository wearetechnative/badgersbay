## Why

ISO policy requires all endpoints (laptops) to be audited 2x per year. Currently, the honeybadger client script generates reports that users must manually email or share via Slack to the IT team. This manual process is error-prone and makes compliance tracking difficult. The server needs to track which systems have submitted complete report sets during audit periods and provide visibility into compliance status.

## What Changes

- Add configurable audit periods (specific months when audits must be completed)
- Implement dual-mode operation: compliance mode (audit-period-based) and legacy mode (date-based)
- Restructure storage from date-based directories to audit-period-based directories with SID identification
- Track completeness of report sets (must include neofetch + lynis + trivy/vulnix)
- Add in-memory compliance cache for fast dashboard queries
- Support X-OS-Type metadata from client uploads (optional with fallback to "unknown")
- Display per-audit-period compliance view showing complete/incomplete systems
- Automatically map uploads to appropriate audit period based on upload date
- Enable compliance mode by default in configuration

## Capabilities

### New Capabilities
- `audit-period-management`: Configuration and tracking of audit periods with specific months when compliance audits must occur
- `report-completeness-validation`: Validation logic to determine if a system has submitted all required reports (neofetch + lynis + one scanner)
- `compliance-dashboard`: Period-based dashboard view showing which systems are compliant vs incomplete per audit period

### Modified Capabilities
- `report-storage`: Dual-mode support - compliance mode uses audit-period structure (`YYYY-MM/sid-username/`), legacy mode uses date-based structure (`hostname-username-YYYYMMDD/`)
- `report-ingestion`: Add X-OS-Type header support (optional, defaults to "unknown") and audit period calculation for incoming uploads
- `status-dashboard`: Dual-mode dashboard - compliance mode shows per-audit-period view, legacy mode shows chronological listing

## Impact

**Storage Structure:**
- Dual-mode operation: compliance mode (`YYYY-MM/sid-username/`) and legacy mode (`hostname-username-YYYYMMDD/`)
- Existing reports in old format remain accessible by switching to legacy mode (`compliance.enabled: false`)
- SID (System ID) extracted from neofetch report's `host` field (fallback to hostname)
- No automatic migration of legacy data - both formats coexist in same `./reports/` directory

**Configuration:**
- New `compliance` section in config.yaml with audit_months and required_reports
- Compliance mode enabled by default in shipped config.yaml (audit_months: [3, 9])
- Fully backwards compatible - can switch to legacy mode by setting `compliance.enabled: false`

**Performance:**
- In-memory cache added to server for fast compliance lookups
- Cache rebuilt on server start and updated on each POST
- Suitable for systemd deployment (long-running service)

**Client Integration:**
- X-OS-Type header support with graceful fallback to "unknown" if not provided
- All curl examples in README updated to include X-OS-Type as best practice
- Existing clients continue to work without modifications
- Upload behavior unchanged from client perspective

**Dashboard:**
- Dual-mode dashboard: compliance mode shows per-audit-period view, legacy mode shows chronological listing
- Compliance dashboard features: audit period selector, summary statistics, completeness filtering
- Legacy dashboard features: auto-refresh, date-based filtering (unchanged)
- Both modes maintain existing report download functionality
- Dashboard automatically switches based on `compliance.enabled` configuration

## Implementation Status

✅ **COMPLETED** - All 88 tasks across 10 implementation groups completed successfully:

1. Configuration and Setup (6/6 tasks) ✓
2. Audit Period Calculation (6/6 tasks) ✓
3. Storage Layer Modifications (8/8 tasks) ✓
4. Report Completeness Validation (8/8 tasks) ✓
5. In-Memory Compliance Cache (10/10 tasks) ✓
6. POST Handler Updates (9/9 tasks) ✓
7. Compliance Dashboard HTML (13/13 tasks) ✓
8. GET Handler Updates (10/10 tasks) ✓
9. Integration Testing (10/10 tasks) ✓
10. Documentation and Configuration (8/8 tasks) ✓

**Key Deliverables:**
- Dual-mode server operation (compliance + legacy)
- Audit period mapping with configurable months
- In-memory compliance cache for performance
- Complete compliance dashboard with filtering
- Full test coverage (audit period, completeness, server startup)
- Comprehensive documentation in README.md
- Production-ready config.yaml with compliance enabled
