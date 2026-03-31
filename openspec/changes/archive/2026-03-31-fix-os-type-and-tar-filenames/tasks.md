## 1. Extract OS type from neofetch data

- [x] 1.1 Locate do_POST() method in honeybadger_server.py (around line 876)
- [x] 1.2 Add OS type extraction logic after X-OS-Type header read but before save_report() call
- [x] 1.3 Check if report_type.lower() == 'neofetch' and data is dict with 'os' field
- [x] 1.4 Extract os_type from data.get('os', fallback_to_header_value)
- [x] 1.5 Log extracted OS type with logger.info() for debugging
- [x] 1.6 Pass extracted os_type to save_report() and compliance_cache.update_system()

## 2. Update tar archive filename format

- [x] 2.1 Locate do_POST_submit_tar() method in honeybadger_server.py (around line 964)
- [x] 2.2 Find tar_filename assignment line (currently f"submission-{timestamp}.tar.gz")
- [x] 2.3 Change prefix from "submission-" to "honeybadger-"
- [x] 2.4 Verify format remains: f"honeybadger-{timestamp}.tar.gz"

## 3. Test OS type extraction (Manual - requires running server)

- [x] 3.1 Create test neofetch JSON with valid os field (e.g., {"os": "NixOS 24.05"})
- [x] 3.2 Upload test neofetch via POST / without X-OS-Type header (see test-manual.sh)
- [x] 3.3 Verify server logs show extracted OS type
- [x] 3.4 Refresh dashboard and verify OS Type column shows correct value
- [x] 3.5 Upload neofetch with both header and JSON os field, verify JSON takes precedence
- [x] 3.6 Upload neofetch without os field, verify falls back to header or "unknown"

## 4. Test tar filename changes (Manual - requires running server)

- [x] 4.1 Create test tar archive with sample reports
- [x] 4.2 Upload via POST /submit-tar endpoint
- [x] 4.3 Verify saved file has honeybadger-{timestamp}.tar.gz format
- [x] 4.4 Check server logs confirm save location
- [x] 4.5 Access compliance dashboard and click TAR badge
- [x] 4.6 Verify downloaded filename includes honeybadger prefix
- [x] 4.7 Test with existing submission-* tar files remain downloadable

## 5. Integration testing (Manual - requires running server)

- [x] 5.1 Run existing test.sh script to verify no regressions
- [x] 5.2 Run existing test-tar-submit.sh with updated expectations
- [x] 5.3 Test full workflow: upload neofetch → upload lynis → upload tar → check dashboard
- [x] 5.4 Verify dashboard refresh shows OS type without server restart
- [x] 5.5 Test with all report types (lynis, neofetch, trivy, vulnix)
- [x] 5.6 Verify backward compatibility with existing stored reports

## 6. Documentation

- [x] 6.1 Update BUGFIXES.md with description of OS type extraction fix
- [x] 6.2 Update BUGFIXES.md with description of tar filename change
- [x] 6.3 Note that no API changes were made (backward compatible)
- [x] 6.4 Document that existing submission-* tar files continue to work
