## Why

The Honeybadger server was designed to aggregate security scans from various systems, but for ISO compliance purposes, only Lynis and Neofetch reports are actually needed. Trivy (container scanning) and Vulnix (NixOS-specific) add unnecessary complexity for the ISO compliance use case.

## What Changes

- Remove Trivy report type support from validation and storage
- Remove Vulnix report type support from validation and storage
- Simplify the "OK" status logic to only require Neofetch + Lynis
- Update dashboard to only display Lynis and Neofetch reports
- Remove Trivy and Vulnix validation logic
- Update documentation to reflect ISO compliance focus

## Capabilities

### New Capabilities
<!-- No new capabilities are being added -->

### Modified Capabilities
- `report-ingestion`: Remove Trivy and Vulnix from accepted report types
- `report-storage`: Remove Trivy and Vulnix file handling
- `status-dashboard`: Simplify system status logic to only check for Lynis + Neofetch
- `health-monitoring`: Update health checks to reflect new report type set

## Impact

- **Code**: Changes to validation logic, storage handlers, dashboard HTML generation, and status calculation
- **Storage**: Existing Trivy/Vulnix reports will remain on disk but won't be displayed or validated for new submissions
- **Clients**: Systems currently submitting Trivy or Vulnix reports will receive validation errors after this change
- **Dashboard**: Status indicators will no longer consider Trivy/Vulnix when marking systems as "OK"
- **Breaking Change**: This is **BREAKING** for any clients submitting Trivy or Vulnix reports
