## Why

The OS type displayed in the compliance dashboard is not updated when new reports arrive. It only refreshes after a server restart, which creates confusion for users monitoring system status. Additionally, tar archive submissions are renamed from user-friendly names (e.g., `honeybadger-lobos-wtoorren-30-03-2026.tar.gz`) to generic timestamps (e.g., `submission-20260330-142931.tar.gz`), making downloaded files harder to identify.

## What Changes

- Extract OS type from neofetch report data during upload instead of relying only on X-OS-Type header
- Maintain original tar filename prefix ("honeybadger-") when saving uploaded archives
- Update cache refresh logic to always read neofetch data for OS type information
- Preserve user-provided tar filenames in download responses for better file identification

## Capabilities

### New Capabilities
<!-- None - this is a bug fix that enhances existing capabilities -->

### Modified Capabilities
- `report-ingestion`: Extract OS type from neofetch JSON payload during single report upload
- `report-storage`: Preserve meaningful tar archive filenames using "honeybadger-" prefix instead of "submission-"
- `compliance-tracking`: Ensure OS type updates immediately on dashboard refresh without requiring server restart

## Impact

**Code Changes:**
- `do_POST()`: Add OS type extraction from neofetch data field
- `do_POST_submit_tar()`: Change tar filename format from `submission-{timestamp}` to `honeybadger-{timestamp}`
- `ComplianceCache.update_system()`: Ensure OS type from neofetch data takes precedence

**User Experience:**
- Dashboard shows correct OS type immediately after report upload
- Downloaded tar files maintain recognizable "honeybadger-" prefix for easier file management
- No breaking changes to API or storage structure

**Backwards Compatibility:**
- Existing stored reports remain unchanged
- Existing tar files with "submission-" prefix continue to work
- API endpoints unchanged (optional X-OS-Type header still supported)
